# Deployment Guide — Prabhasha Nexus

## 1. Environments

| Environment | Database | Media | Purpose |
|-------------|----------|-------|---------|
| Local | SQLite (default) or MySQL | `backend/uploads/` | development |
| CI | SQLite | temp directories | automated tests |
| Production | Managed MySQL 8 | persistent disk | live |

## 2. Required Environment Variables

Copy `.env.example` and set at minimum:

```
FLASK_ENV=production
SECRET_KEY=<long random value>
JWT_SECRET_KEY=<another long random value>
DATABASE_URL=mysql+pymysql://user:pass@host:3306/db?charset=utf8mb4
CORS_ORIGINS=https://your-frontend-domain
FRONTEND_URL=https://your-frontend-domain
ADMIN_EMAIL=<owner email>
ADMIN_PASSWORD=<strong initial password>
ANALYTICS_SALT=<random value>
```

Optional integrations: `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GITHUB_TOKEN`, `N8N_*`, `SMTP_*`.

Docker Compose additionally reads `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD` and
`MYSQL_ROOT_PASSWORD`.

**Never commit `.env`.** Rotate the seeded admin password immediately after first login.
Set `SEED_ON_START=false` after the first successful deployment.

## 3. Docker Compose (self-hosted)

```bash
cp .env.example .env
# edit .env: secrets, MySQL passwords, CORS_ORIGINS, FRONTEND_URL
docker compose up --build -d
docker compose ps
```

The backend entrypoint waits for the MySQL health check, applies `flask db upgrade`, and
seeds verified portfolio data when `SEED_ON_START=true`. Manual equivalents:

```bash
docker compose exec backend flask --app wsgi.py db upgrade
docker compose exec backend flask --app wsgi.py seed
docker compose exec backend flask --app wsgi.py backup create
```

Services:

| Service | Image / build | Port | Persistent volume |
|---------|---------------|------|-------------------|
| `db` | `mysql:8.0` | internal 3306 | `mysql_data` → `/var/lib/mysql` |
| `backend` | `docker/backend.Dockerfile` (Gunicorn) | 5000 | `nexus_data` → `/data` |
| `frontend` | `docker/frontend.Dockerfile` (Nginx) | 8080 | none (static image) |

URLs: frontend `http://localhost:8080`, backend `http://localhost:5000`,
Swagger UI `http://localhost:5000/api/docs`.

### Persistent storage

Uploads, backups, knowledge documents and the retrieval index live under `/data` in the
backend container and are backed by the `nexus_data` volume:

```
UPLOAD_DIR=/data/uploads
BACKUP_DIR=/data/backups
KNOWLEDGE_DIR=/data/knowledge
FAISS_INDEX_DIR=/data/index
```

`S3_*` settings are reserved for a future storage adapter; the current release stores
media on local disk only. On hosts with ephemeral disks, mount a persistent disk or copy
`nexus_data` off the host regularly.

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
- Pre-deploy command: `flask --app wsgi.py db upgrade`
- Seed once via a Render shell, then set `SEED_ON_START=false`: `flask --app wsgi.py seed`
- Add all environment variables, including a strong `SECRET_KEY` and `JWT_SECRET_KEY`.
- Attach a persistent disk mounted at `/var/data` and set:
  ```
  UPLOAD_DIR=/var/data/uploads
  BACKUP_DIR=/var/data/backups
  KNOWLEDGE_DIR=/var/data/knowledge
  FAISS_INDEX_DIR=/var/data/index
  ```

### 4.3 Frontend (Static Site)
- Root directory: `frontend`
- Publish directory: `.`
- Point the frontend at the backend before `config.js` loads:
  ```html
  <script>window.PRABHASHA_API_BASE = "https://<backend>.onrender.com/api/v1";</script>
  ```
  or edit `assets/js/config.js` directly.
- Add the frontend domain to backend `CORS_ORIGINS`.

## 5. Production Checks

- [ ] HTTPS enforced by host
- [ ] Strong `SECRET_KEY` / `JWT_SECRET_KEY`
- [ ] Seed admin password changed
- [ ] `CORS_ORIGINS` restricted to real domains
- [ ] `FLASK_ENV=production`
- [ ] `DEBUG=false`
- [ ] `SEED_ON_START=false` after first deploy
- [ ] Media/backup storage persistent
- [ ] Database backups scheduled and restore-tested
- [ ] Rate limits reviewed
- [ ] Logs and uptime monitored

## 6. Migrations

```bash
cd backend

# create (development only)
flask --app wsgi.py db migrate -m "describe change"

# apply (all environments)
flask --app wsgi.py db upgrade

# rollback one revision
flask --app wsgi.py db downgrade
```

Docker Compose applies migrations automatically. Run `db upgrade` in CI against a
throwaway database and in every production release.

## 7. Backup & Restore

Application-level JSON backup:

```bash
flask --app wsgi.py backup create
flask --app wsgi.py backup list
```

Files are written to `BACKUP_DIR` (`backend/backups/` locally, `/data/backups` in Docker).
The admin API also exposes `POST /api/v1/admin/backup`.

MySQL logical dump:

```bash
mysqldump -h HOST -u USER -p --single-transaction --routines --triggers DB > nexus.sql
mysql -h HOST -u USER -p DB < nexus.sql
```

Store dumps encrypted and outside the repository.

Restore checklist:
1. Put the app in maintenance mode or stop writers.
2. Restore the database dump.
3. Restore uploads and backups from persistent storage.
4. Rebuild the knowledge index: `flask --app wsgi.py knowledge rebuild`.
5. Run `flask --app wsgi.py db upgrade` if the schema is older.

## 8. CI/CD

`.github/workflows/ci.yml` runs on pushes and pull requests to `main`:

- installs backend dependencies and runs the SQLite migration
- runs the full Pytest suite
- checks all frontend JavaScript files with `node --check`
- builds the backend and frontend Docker images

Add deployment secrets in the hosting provider, never in the workflow file.

## 9. Rollback

1. Deploy the previous container image or commit.
2. If the schema changed, `flask --app wsgi.py db downgrade` to the matching revision
   (only if that revision is reversible).
3. Restore the database backup when a destructive migration occurred.

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| 401 on admin calls | expired access token | refresh via `/api/v1/auth/refresh` |
| 429 on login | rate limit | wait or adjust `RATE_LIMIT_LOGIN` |
| Backend restarts at boot | database unavailable | check `docker compose logs db` and health check |
| 502 from Nginx | backend not healthy | check `docker compose logs backend` |
| Uploads lost after deploy | ephemeral disk | mount persistent disk; keep `nexus_data` |
| AI answers generic | no LLM key | set `GROQ_API_KEY` or `OPENROUTER_API_KEY` |
| AI retrieval is keyword-based | no embedding model | install `requirements-ai.txt` and rebuild index |
| GitHub data stale | cache TTL | `POST /api/v1/admin/github/refresh` |
| CORS blocked | origin not allowlisted | update `CORS_ORIGINS` |
