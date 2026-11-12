# Prabhasha Nexus

**AI-Powered Personal Portfolio & Intelligence Management Platform**

Prabhasha Nexus is a full-stack, production-oriented portfolio platform for **Muwagamage Tharushi Prabhasha Dilshani** — AI/ML Engineer, Data Science Enthusiast, Python Developer, and Generative AI Developer.

It combines a premium public portfolio, a complete admin dashboard, a versioned Flask REST API, a MySQL relational database, an AI portfolio assistant (RAG + LangGraph multi-agent routing), portfolio analytics, GitHub integration, and n8n workflow automation.

---

## Key Features

### Public Portfolio
- Dark/light glassmorphism design with persisted theme
- Home, About, Skills, Projects, Certificates, Education/Experience, Research, Blog, Contact
- Dynamic content loaded exclusively from `/api/v1/` REST endpoints
- Project detail pages with architecture, metrics, challenges, and future work
- Certificate gallery with PDF/image previews and verification links
- Blog with categories, tags, reading time, related posts
- Contact form with validation, spam protection, and database persistence
- Resume/CV download tracking
- AI portfolio chatbot with source-aware answers
- Privacy-conscious analytics event tracking
- Responsive, accessible, SEO-aware markup

### Admin Dashboard
- JWT authentication with role-based access control (admin/editor/viewer)
- Dashboard overview driven by real database statistics
- 24 management modules: profile, projects, skills, certificates, education, experience, achievements, research, blog, media, messages, testimonials, newsletter, resumes, analytics, GitHub, AI center, knowledge base, automation, notifications, users, activity logs, settings, backups
- Full CRUD with search, filtering, sorting, pagination, publish/archive/featured states
- Confirmation dialogs, toast notifications, form validation, empty/loading/error states

### AI Intelligence Center
- Retrieval-Augmented Generation over approved knowledge documents
- PDF upload, text extraction, chunking, embeddings, FAISS index (with graceful numpy fallback)
- LangGraph multi-agent routing with deterministic fallback when no LLM key is present
- AI content drafting (remains draft until approved)
- AI resume/job-description matching — never fabricates experience

### Integrations
- Official GitHub API with server-side caching and rate-limit handling
- n8n authenticated webhooks with execution logging
- Swagger/OpenAPI documentation

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript ES6+, Bootstrap 5, Fetch API, Chart.js, AOS, Font Awesome |
| Backend | Python 3, Flask, Blueprints, SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flask-CORS, Flask-Limiter, Marshmallow, Gunicorn |
| Database | MySQL 8 (SQLite for local dev/tests), Alembic migrations |
| AI | LangChain, LangGraph, FAISS, HuggingFace embeddings, Groq, OpenRouter (all optional with fallbacks) |
| Automation | n8n webhooks, SMTP email |
| DevOps | Git, GitHub Actions, Docker, Docker Compose, Render, Pytest |

---

## Folder Structure

```
prabhasha-nexus/
├── frontend/
│   ├── index.html              # Home / About / Skills / Highlights
│   ├── pages/                  # projects, certificates, education, research, blog, contact...
│   ├── admin/                  # login.html + index.html (admin SPA)
│   └── assets/                 # css, js, images, fonts
├── backend/
│   ├── app/
│   │   ├── __init__.py         # application factory
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── models/             # SQLAlchemy models
│   │   ├── schemas/            # Marshmallow validation
│   │   ├── routes/             # versioned API blueprints
│   │   ├── services/           # business logic
│   │   ├── repositories/       # query helpers
│   │   ├── ai/                 # RAG, embeddings, LangGraph agents
│   │   ├── automation/         # n8n webhook client
│   │   ├── middleware/         # auth, audit, security headers
│   │   └── utils/              # responses, errors, pagination, files
│   ├── migrations/             # Alembic
│   ├── tests/                  # Pytest suite
│   ├── uploads/                # local media (gitignored)
│   ├── requirements.txt
│   ├── run.py
│   └── wsgi.py
├── database/
│   ├── schema/                 # reference SQL schema
│   └── seeds/                  # seed data notes
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── deployment/
│   └── development/
├── docker/
├── scripts/
├── .env.example
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## Installation

### Prerequisites
- Python 3.11+ (tested on 3.13)
- MySQL 8 (optional for local; SQLite is the default)
- Docker + Docker Compose (optional)

### 1. Clone
```bash
git clone https://github.com/prabhasha-2001/prabhasha-nexus.git
cd prabhasha-nexus
```

### 2. Backend setup
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
copy ..\.env.example .env      # Windows
# cp ../.env.example .env      # Linux/macOS
```

Edit `.env` (at repository root or `backend/.env`) with real values.

### 3. Database setup
```bash
# Initialize migrations (first time only, already committed in repo)
flask --app wsgi.py db upgrade

# Create the initial administrator + verified portfolio seed data
flask --app wsgi.py seed
```

For MySQL, set `DATABASE_URL`:
```
mysql+pymysql://user:password@127.0.0.1:3306/prabhasha_nexus?charset=utf8mb4
```

### 4. Run backend
```bash
python run.py
# API: http://localhost:5000/api/v1
# Swagger UI: http://localhost:5000/api/docs
```

### 5. Run frontend
Serve the `frontend/` directory with any static server:
```bash
cd frontend
python -m http.server 5500
# http://localhost:5500
```
The frontend reads the API base URL from `window.PRABHASHA_API_BASE` (default `http://localhost:5000/api/v1`).

Default seed administrator credentials come from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in `.env`. Change the password immediately after first login.

---

## Docker

```bash
copy .env.example .env
docker compose up --build
# Frontend: http://localhost:8080
# Backend:  http://localhost:5000
# MySQL:    localhost:3306
```

Then seed once:
```bash
docker compose exec backend flask --app wsgi.py seed
```

See `docs/deployment/deployment-guide.md` for production guidance.

---

## API

- Base path: `/api/v1/`
- Interactive docs: `/api/docs`
- OpenAPI JSON: `/api/openapi.json`
- Documentation: `docs/api/api-documentation.md`

Authentication uses JWT bearer tokens. Public read endpoints are unauthenticated and rate-limited; all admin endpoints require a valid token and appropriate role.

---

## Testing

```bash
cd backend
pytest -q
```

Tests use an isolated SQLite database and mock external AI/GitHub/n8n calls. No real credentials are required.

---

## Environment Configuration

All configuration is environment-driven. See `.env.example` for the complete list. Secrets are never committed and never exposed to the frontend.

AI, GitHub, SMTP, and n8n integrations degrade gracefully:
- No LLM key → deterministic retrieval-grounded assistant
- No GitHub token → unauthenticated cached API calls (rate-limited)
- No n8n URL → automations recorded as `not_configured`
- No SMTP → emails recorded as skipped

---

## Security

- Password hashing (Werkzeug PBKDF2)
- JWT access/refresh tokens with revocation checks
- Role-based access control
- Login and endpoint rate limiting
- CORS allowlist
- Security headers (CSP, X-Frame-Options, nosniff, referrer policy)
- Upload validation by magic bytes, size limits, sanitized filenames
- SQL injection protection via ORM parameterisation
- Audit logging of administrative actions
- Environment-based secrets

---

## Screenshots

Screenshots will be added under `docs/screenshots/` after UI completion:
- Home (dark / light)
- Projects gallery & detail
- Certificates gallery
- Admin dashboard
- AI chatbot
- Analytics charts

---

## Documentation

| Document | Path |
|----------|------|
| System Architecture | `docs/architecture/system-architecture.md` |
| Database Design | `docs/database/database-design.md` |
| API Documentation | `docs/api/api-documentation.md` |
| Deployment Guide | `docs/deployment/deployment-guide.md` |
| Development Roadmap | `docs/development/development-roadmap.md` |

---

## Roadmap

- [x] Phase 1 — Foundation, docs, tooling
- [x] Phase 2 — Database & backend foundation
- [x] Phase 3 — Core REST APIs, auth, validation
- [x] Phase 4 — Public frontend
- [x] Phase 5 — Admin dashboard
- [x] Phase 6 — AI Intelligence Center (RAG, LangGraph)
- [x] Phase 7 — Analytics, GitHub, n8n
- [x] Phase 8 — Testing, security, Docker, deployment

Future improvements:
- Two-factor authentication
- Object storage adapter (S3/R2) for media
- Contribution heatmap from GitHub GraphQL
- Multi-language portfolio (Sinhala/English)
- Predictive engagement analytics

---

## Owner

**Muwagamage Tharushi Prabhasha Dilshani**
AI/ML Engineer · Data Science Enthusiast · Python Developer · Generative AI Developer
Kaduwela, Sri Lanka
[GitHub](https://github.com/prabhasha-2001) · [LinkedIn](https://linkedin.com/in/prabhasha-dilshani-7258593a6)

---

## License

Personal project. All portfolio content belongs to the owner. Code provided for the owner's use.
