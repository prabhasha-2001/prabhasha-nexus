#!/bin/sh
set -eu

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying database migrations..."
  flask --app wsgi.py db upgrade
fi

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "Seeding verified portfolio data..."
  flask --app wsgi.py seed
fi

exec gunicorn \
  --workers "${GUNICORN_WORKERS:-3}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --bind "0.0.0.0:${PORT:-5000}" \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
