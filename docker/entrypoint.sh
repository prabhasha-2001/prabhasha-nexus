#!/bin/sh
set -eu

wait_for_database() {
  python - <<'PY'
import os
import sys
import time

from sqlalchemy import create_engine, text

uri = (os.getenv("DATABASE_URL") or "").strip()
if not uri:
    from app.config import Config
    uri = Config.SQLALCHEMY_DATABASE_URI

# SQLite does not require a network wait.
if uri.startswith("sqlite"):
    sys.exit(0)

retries = int(os.getenv("DB_WAIT_RETRIES", "30"))
delay = float(os.getenv("DB_WAIT_DELAY_SECONDS", "2"))
last_error = None
for attempt in range(1, retries + 1):
    try:
        engine = create_engine(uri, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        print(f"Database ready (attempt {attempt}/{retries}).")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001 - startup diagnostic
        last_error = exc
        print(f"Database not ready (attempt {attempt}/{retries}): {type(exc).__name__}: {exc}")
        if attempt < retries:
            time.sleep(delay)

print(f"Database connection failed after {retries} attempts: {last_error}")
sys.exit(1)
PY
}

wait_for_database

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying database migrations..."
  if ! flask --app wsgi.py db upgrade; then
    echo "Database migration failed."
    exit 1
  fi
fi

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "Seeding verified portfolio data..."
  if ! flask --app wsgi.py seed; then
    echo "Database seed failed."
    exit 1
  fi
fi

exec gunicorn \
  --workers "${GUNICORN_WORKERS:-3}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --bind "0.0.0.0:${PORT:-5000}" \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
