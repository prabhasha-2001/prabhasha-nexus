# Prabhasha Nexus

**AI-Powered Personal Portfolio & Intelligence Management Platform**

Prabhasha Nexus is a full-stack portfolio and content platform for **Muwagamage Tharushi Prabhasha Dilshani** — AI/ML Engineer, Data Science Enthusiast, Python Developer and Generative AI Developer.

It combines a public portfolio, a role-based admin dashboard, a versioned Flask REST API, a MySQL/SQLite database, a grounded AI assistant, privacy-conscious analytics, GitHub integration and n8n workflow automation. Portfolio facts are seeded only from verified owner data; unverified features degrade gracefully instead of inventing content.

---

## Highlights

### Public portfolio
- Dark/light design system with persisted theme, responsive navigation and accessible markup
- Home, About, Projects (+ detail), Research, Certificates, Blog, Contact
- Content loaded from `/api/v1/` REST endpoints with loading, empty and error states
- Project case studies with architecture, metrics, challenges and future work
- Certificate gallery with verification links
- Contact form and newsletter signup with validation, rate limiting and persistence
- CV download with tracked events
- Grounded AI portfolio assistant with source labels
- First-party analytics events and GitHub activity panel

### Admin dashboard
- JWT authentication with refresh tokens and admin/editor/viewer role enforcement
- Dashboard KPIs, traffic chart, popular content and recent activity from real data
- CRUD modules for profile, projects, research, blog, education, experience, skills, skill groups, certificates, testimonials, achievements, categories and tags
- Inbox for contact messages and newsletter subscribers
- Media library and CV/resume version management
- Analytics overview with CSV export
- GitHub profile/repository cache viewer and refresh
- AI studio, knowledge base, conversations and generation review
- Automation workflows and execution logs
- Users, activity audit trail, system settings and backups

### AI intelligence
- Retrieval grounding over approved portfolio data and uploaded knowledge documents
- Lexical retrieval and deterministic answer fallback when no embedding/LLM provider is configured
- Optional Groq/OpenRouter generation through `requests`
- Knowledge upload (PDF/TXT/Markdown), approval workflow and index rebuild
- Content drafting that stays in draft until a human approves it
- Resume/job-description keyword analysis without fabricating experience

### Operations
- Alembic migrations, idempotent seed command and health endpoint
- Central error envelope, rate limiting, audit logging and security headers
- Docker Compose stack with MySQL, Gunicorn and Nginx
- GitHub Actions CI for tests, JavaScript syntax and Docker builds

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3 custom design system, vanilla JavaScript ES6+, Fetch API |
| Backend | Python 3.11+, Flask, Blueprints, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS, Flask-Limiter, Marshmallow, Gunicorn |
| Database | MySQL 8 in production, SQLite for local development and tests, Alembic migrations |
| AI | Optional Groq/OpenRouter LLMs, optional sentence-transformers embeddings, lexical BM25-style fallback |
| Automation | n8n webhooks, SMTP email |
| DevOps | Docker, Docker Compose, Nginx, GitHub Actions, Pytest |

No frontend build step or npm dependency is required.

---

## Project Structure

```
prabhasha-nexus/
├── frontend/
│   ├── index.html, about.html, projects.html, project.html
│   ├── research.html, certificates.html, blog.html, contact.html
│   ├── admin/index.html              # admin SPA (hash routing)
│   └── assets/
│       ├── css/styles.css            # public design system
│       ├── css/admin.css             # admin shell
│       └── js/{config,api,ui,pages,admin}.js
├── backend/
│   ├── app/
│   │   ├── __init__.py               # application factory
│   │   ├── config.py                 # environment profiles
│   │   ├── extensions.py
│   │   ├── models/                   # SQLAlchemy models
│   │   ├── schemas/                  # Marshmallow validation
│   │   ├── routes/                   # public, auth, admin, AI, integrations
│   │   ├── services/                 # CRUD, auth, seed, analytics, backups
│   │   ├── ai/                       # embeddings, LLM, RAG, chat, generation
│   │   ├── automation/               # n8n client
│   │   └── utils/                    # responses, errors, pagination, security
│   ├── migrations/                   # Alembic
│   ├── tests/                        # 51 pytest tests
│   ├── requirements.txt
│   ├── wsgi.py
│   └── run.py
├── docker/                           # backend/frontend Dockerfiles + nginx/entrypoint
├── docker-compose.yml
├── docs/
├── .github/workflows/ci.yml
└── .env.example
```

---

## Quick Start

### Prerequisites
- Python 3.11+ (tested on 3.13)
- Optional: MySQL 8, Docker and Docker Compose

### 1. Clone and configure

```powershell
git clone https://github.com/prabhasha-2001/prabhasha-nexus.git
cd prabhasha-nexus
Copy-Item .env.example .env
```

Edit `.env` and set at least strong `SECRET_KEY`, `JWT_SECRET_KEY`, `ADMIN_EMAIL` and `ADMIN_PASSWORD`. SQLite is used locally when `DATABASE_URL` and `DB_*` are empty. For MySQL, prefer `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` (assembled safely via SQLAlchemy) when passwords contain special characters.

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
flask --app wsgi.py db upgrade
flask --app wsgi.py seed
python run.py
```

- API: `http://localhost:5000/api/v1`
- Swagger UI: `http://localhost:5000/api/docs`
- OpenAPI JSON: `http://localhost:5000/api/openapi.json`
- Health: `http://localhost:5000/api/v1/health`

### 3. Frontend

Serve the `frontend/` directory with any static server:

```bash
cd frontend
python -m http.server 8000
```

Open `http://localhost:8000` for the public site and `http://localhost:8000/admin/index.html` for the dashboard.

On ports `8000`, `5500`, `3000` or `5173` the frontend calls `http://localhost:5000/api/v1`. Set `window.PRABHASHA_API_BASE` before loading `config.js` to override this. On other origins (including the Docker frontend) it uses same-origin `/api/v1`, which Nginx proxies to the backend.

### 4. Sign in

Use the initial admin credentials from `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`), then change the password immediately. Seed data is idempotent and contains only verified profile, education, skills, projects, research and workflow records.

---

## Docker

```powershell
Copy-Item .env.example .env
# edit secrets and MySQL passwords in .env (MYSQL_* / ADMIN_*; passwords with @, :, /, etc. are supported)
docker compose up -d --build
docker compose ps
```

Services:
- `db` — MySQL 8 with the `mysql_data` volume
- `backend` — Gunicorn on port 5000, data volume `nexus_data` (waits for DB, runs migrations, optional seed)
- `frontend` — Nginx on port 8080, proxying `/api/` and `/uploads/` to the backend

Compose builds the MySQL URL safely from `DB_*` components in the app config (so special characters in `MYSQL_PASSWORD` are handled correctly) and starts the backend only after DB readiness/migrations succeed. `SEED_ON_START=true` seeds once idempotently; set it to `false` after the first successful deployment.

URLs: public site `http://localhost:8080`, backend `http://localhost:5000`, health `http://localhost:5000/api/v1/health`.

---

## Testing

```bash
cd backend
python -m pytest -q
```

The suite currently has **51 passing tests** covering public APIs, auth/JWT rotation, RBAC, admin CRUD, uploads, analytics, integrations and AI fallbacks. Tests use an isolated SQLite database and never require real AI, GitHub, SMTP or n8n credentials.

---

## Configuration

All configuration is environment-driven; see `.env.example`. Key groups:

| Group | Variables |
|-------|-----------|
| Flask/JWT | `SECRET_KEY`, `JWT_SECRET_KEY`, token lifetimes |
| Database | `DATABASE_URL`, `MYSQL_*` for Compose |
| CORS | `CORS_ORIGINS`, `FRONTEND_URL` |
| Admin seed | `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` |
| Limits | `RATE_LIMIT_*`, `MAX_CONTENT_LENGTH_MB` |
| AI | `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `EMBEDDINGS_ENABLED`, `AI_TOP_K` |
| Integrations | `GITHUB_TOKEN`, `N8N_*`, `SMTP_*` |
| Storage | `UPLOAD_DIR`, `BACKUP_DIR`, `S3_*` |

### Graceful degradation

| Missing configuration | Behaviour |
|-----------------------|-----------|
| No LLM key | Deterministic, retrieval-grounded assistant and template drafts |
| No embedding model | Lexical retrieval fallback |
| No GitHub token | Unauthenticated cached GitHub API calls with rate-limit handling |
| No n8n URL | Workflow runs recorded as `not_configured` |
| No SMTP | Email delivery recorded as skipped |

AI, GitHub, SMTP and n8n failures never break core portfolio or admin functionality.

---

## API

- Base path: `/api/v1/`
- Envelope: `{ "success": true, "data": ..., "meta": ... }`
- Pagination meta: `{ page, per_page, total, pages, has_next, has_prev }`
- Auth: `Authorization: Bearer <access_token>`
- Public endpoints are unauthenticated and rate-limited; admin endpoints require a valid token and role.

Documentation:
- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/openapi.json`
- Reference: `docs/api/api-documentation.md`

---

## Security

- Werkzeug PBKDF2 password hashing
- Short-lived access tokens and revocable refresh tokens
- Role-based access control (admin/editor/viewer)
- Login, AI, contact and default rate limits
- CORS allowlist
- Security headers (CSP, `X-Frame-Options`, `nosniff`, referrer policy)
- Upload extension, size and magic-byte validation with sanitized filenames
- ORM parameterisation and audit logging
- Environment-only secrets; `.env` is gitignored

Never commit `.env` or real credentials. Rotate the seeded administrator password and any integration tokens before going live.

---

## Deployment

See `docs/deployment/deployment-guide.md` for Docker, Render and MySQL guidance, persistent storage notes, migrations, backups, rollback and troubleshooting.

Production checklist:
- [ ] HTTPS enforced
- [ ] Strong `SECRET_KEY` / `JWT_SECRET_KEY`
- [ ] Seed admin password changed
- [ ] `CORS_ORIGINS` restricted to real domains
- [ ] `DEBUG=false`
- [ ] Persistent media/backup storage configured
- [ ] Database backups scheduled and tested
- [ ] Logs and rate limits monitored

---

## Roadmap

- [x] Phase 1 — Foundation, docs and tooling
- [x] Phase 2 — Database and backend foundation
- [x] Phase 3 — Core REST APIs, auth and validation
- [x] Phase 4 — Public frontend
- [x] Phase 5 — Admin dashboard
- [x] Phase 6 — AI intelligence center
- [x] Phase 7 — Analytics, GitHub and n8n integrations
- [x] Phase 8 — Testing, security, Docker, CI and deployment docs

Post-launch backlog: two-factor authentication, S3/R2 media adapter, GitHub contribution heatmap, Sinhala/English switching, predictive analytics and scheduled database backups.

---

## Documentation

| Document | Path |
|----------|------|
| System architecture | `docs/architecture/system-architecture.md` |
| Database design | `docs/database/database-design.md` |
| API reference | `docs/api/api-documentation.md` |
| Deployment guide | `docs/deployment/deployment-guide.md` |
| Development roadmap | `docs/development/development-roadmap.md` |

---

## Owner

**Muwagamage Tharushi Prabhasha Dilshani**

AI/ML Engineer · Data Science Enthusiast · Python Developer · Generative AI Developer

Kaduwela, Sri Lanka
[GitHub](https://github.com/prabhasha-2001) · [LinkedIn](https://linkedin.com/in/prabhasha-dilshani-7258593a6)

---

## License

Personal project. All portfolio content belongs to the owner. Code is provided for the owner's use.
