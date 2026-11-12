FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    FLASK_APP=wsgi.py

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/ /app/
COPY docker/entrypoint.sh /usr/local/bin/nexus-entrypoint
RUN chmod +x /usr/local/bin/nexus-entrypoint \
    && mkdir -p /data/uploads /data/backups /data/knowledge /data/index \
    && groupadd --system nexus \
    && useradd --system --gid nexus --home-dir /app nexus \
    && chown -R nexus:nexus /app /data

ENV UPLOAD_DIR=/data/uploads \
    BACKUP_DIR=/data/backups \
    KNOWLEDGE_DIR=/data/knowledge \
    FAISS_INDEX_DIR=/data/index \
    GUNICORN_WORKERS=3

USER nexus

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:5000/api/v1/health || exit 1

ENTRYPOINT ["nexus-entrypoint"]
