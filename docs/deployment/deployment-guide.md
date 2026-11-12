# Deployment Guide — Prabhasha Nexus

## 1. Environments

| Environment | Database | Media | Purpose |
|-------------|----------|-------|---------|
| Local | SQLite (default) or MySQL | local `uploads/` | development |
| CI | SQLite | temp | automated tests |
| Production | Managed MySQL 8 | persistent disk or S3 | live |

## 2. Required Environment Variables

Copy `.env.example` and set at minimum:

```
FLASK_ENV=production
SECRET_KEY=<long random>
JWT_SECRET_KEY=<long random>
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
CORS_ORIGINS=https://your-frontend-domain
FRONTEND_URL=https://your-frontend-domain
ADMIN_EMAIL=<owner email>
ADMIN_PASSWORD=<strong initial password>
ANALYTICS_SALT=<random>
```

Optional: `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GITHUB_TOKEN`, `N8N_*`, `SMTP_*`, `S3_*`.

**Never commit `.env`.** Rotate the seed admin password after first login.

## 3. Docker Compose (self-hosted)

```bash
copy .env.example .env
# edit .env
docker compose up --build -d
docker compose exec backend flask --app wsgi.py db upgrade
docker compose exec backend flask --app wsgi.py seed
```

Services:
- `mysql` — MySQL 8 with persistent volume `mysql_data`
- `backend` — Gunicorn, health check `/api/v1/health`
- `frontend` — Nginx serving static files, proxies `/api/` to backend, persistent volume `uploads_data`

URLs: frontend `http://localhost:8080`, backend `http://localhost:5000`.

### Persistent storage
- MySQL data: named volume.
- Uploads: mount `uploads_data` to `/app/uploads` and set `UPLOAD_DIR=/app/uploads`.
- For Render (ephemeral disk), use an S3-compatible bucket:
  ```
  MEDIA_STORAGE_BACKEND=s3
  S3_ENDPOINT_URL=...
  S3_BUCKET=...
  S3_ACCESS_KEY=...
  S3_SECRET_KEY=...
  S3_REGION=...
  ```
  Until configured, uploaded files are local and **not durable** on ephemeral hosts. The admin UI marks storage backend in settings.

## 4. Render Deployment

### 4.1 MySQL
1. Create a Render MySQL instance.
2. Copy the internal connection URL.
3. Set `DATABASE_URL=mysql+pymysql://...` on the backend service.

### 4.2 Backend (Web Service)
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn -w 3 -t 120 -b 0.0.0.0:$PORT wsgi:app`
- Health check path: `/api/v1/health`
- Add all environment variables.
- Pre-deploy command: `flask --app wsgi.py db upgrade`
- Seed once via a Render shell: `flask --app wsgi.py seed`
- Attach a persistent disk (e.g. `/var/data`) and set `UPLOAD_DIR=/var/data/uploads`, `FAISS_INDEX_DIR=/var/data/index`, `KNOWLEDGE_DIR=/var/data/documents`. Or use S3.

### 4.3 Frontend (Static Site)
- Root directory: `frontend`
- Publish directory: `.`
- Set `window.PRABHASHA_API_BASE` (in `assets/js/config.js`) to `https://<backend>.onrender.com/api/v1`
- Add frontend domain to backend `CORS_ORIGINS`.

## 5. Production Checks

- [ ] HTTPS enforced by host
- [ ] Strong `SECRET_KEY` / `JWT_SECRET_KEY`
- [ ] Seed admin password changed
- [ ] `CORS_ORIGINS` restricted to real domains
- [ ] `FLASK_ENV=production`
- [ ] `DEBUG=false`
- [ ] Media storage persistent
- [ ] Database backups scheduled
- [ ] Rate limits reviewed
- [ ] Logs monitored

## 6. Migrations

```bash
# create (development)
flask --app wsgi.py db migrate -m "describe change"
# apply (all environments)
flask --app wsgi.py db upgrade
# rollback one revision
flask --app wsgi.py db downgrade
```

Run `db upgrade` in CI (against a throwaway DB) and in the release step.

## 7. Backup & Restore

Application-level JSON backup:
```bash
flask --app wsgi.py backup create
# files stored in backend/backups/
```
Or via admin API `POST /api/v1/admin/backup`.

MySQL logical dump:
```bash
mysqldump -h HOST -u USER -p --single-transaction --routines --triggers DB > nexus.sql
mysql -h HOST -u USER -p DB < nexus.sql
```
Store dumps encrypted and outside the repository.

Restore checklist:
1. Put the app in maintenance mode / stop writers.
2. Restore DB dump.
3. Restore uploads / object storage.
4. Rebuild RAG index: `flask --app wsgi.py knowledge rebuild`.
5. Run `flask --app wsgi.py db upgrade` if schema is older.

## 8. CI/CD

`.github/workflows/ci.yml` runs on push/PR:
- installs backend dependencies
- runs `pytest`
- runs a syntax/import smoke check
- optionally builds Docker images

Add repository secrets for deployment if continuous deploy is enabled. Never store secrets in the workflow file.

## 9. Rollback

1. Deploy the previous container image / commit.
2. If schema changed, run `flask db downgrade` to the matching revision (only if the revision is reversible).
3. Restore DB backup when a destructive migration occurred.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 401 on admin calls | expired access token | refresh via `/auth/refresh` |
| 429 on login | rate limit | wait or adjust `RATE_LIMIT_LOGIN` |
| Uploads lost after deploy | ephemeral disk | configure persistent disk/S3 |
| AI answers generic | no LLM key | set `GROQ_API_KEY` or `OPENROUTER_API_KEY` |
| GitHub data stale | cache TTL | `POST /admin/github/refresh` |
| CORS blocked | origin not allowlisted | update `CORS_ORIGINS` |
