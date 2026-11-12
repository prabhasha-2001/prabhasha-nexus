# Development Roadmap — Prabhasha Nexus

Each phase ends with verification, documentation updates, a focused commit and a push to
`https://github.com/prabhasha-2001/prabhasha-nexus.git`.

Status legend: DONE = implemented and verified; PLANNED = not yet implemented.

## Phase 1 — Foundation [DONE]
- Workspace inspection, Git initialization, remote verification
- Directory structure (frontend/backend/database/docs/docker/scripts)
- `.gitignore`, `.env.example`
- README, architecture, database, API and deployment documentation
- **Checkpoint 1**

## Phase 2 — Database & Backend Foundation [DONE]
- Flask application factory and config profiles
- Extensions: SQLAlchemy, Migrate, JWT, CORS, Limiter, Marshmallow
- Models covering identity, portfolio, blog, media, analytics, AI, automation and system data
- Alembic migration and idempotent seed command using verified owner data only
- Centralized error handling, response envelope and health endpoint
- **Checkpoint 2**

## Phase 3 — Core REST APIs [DONE]
- Auth: login, refresh, logout, me, change-password, forgot/reset
- Public read APIs for every portfolio resource
- Admin CRUD APIs with RBAC, filtering, sorting and pagination
- Contact, newsletter and media uploads with validation
- Pytest coverage for auth, CRUD, validation and uploads
- **Checkpoint 3**

## Phase 4 — Public Frontend [DONE]
- Design system, dark/light theme with persistence
- Home, About, Skills, Projects (+ detail), Certificates, Education/Experience,
  Research, Blog and Contact
- Fetch API integration with loading, empty and error states
- Responsive navigation, accessible markup and scroll animations
- **Checkpoint 4**

## Phase 5 — Admin Dashboard [DONE]
- JWT login, refresh support and guarded views
- Dashboard KPIs from real data plus traffic charts
- Content, inbox, intelligence, growth and operations modules with CRUD, filters,
  pagination, confirmations and toasts
- **Checkpoint 5**

## Phase 6 — AI Intelligence Center [DONE]
- RAG pipeline with PDF/TXT/Markdown upload, extraction, chunking and indexing
- Public chatbot with source-aware, grounded answers
- Deterministic fallback when no LLM or embedding provider is configured
- AI content drafts requiring human review
- Resume/JD matching without fabrication
- Mock-based and fallback tests
- **Checkpoint 6**

## Phase 7 — Analytics & Integrations [DONE]
- Privacy-conscious event tracking and aggregation
- Admin analytics dashboard, CSV export and report payload
- GitHub API with caching and rate-limit handling
- n8n webhook automation center with execution logs
- Notification and backup management
- **Checkpoint 7**

## Phase 8 — Testing, Security, Deployment [DONE]
- Full Pytest suite (51 passing tests) for auth, RBAC, CRUD, uploads, analytics,
  integrations and AI fallbacks
- Security hardening: headers, upload validation, rate limits and audit logs
- Backend/frontend Dockerfiles, Compose stack, Nginx proxy and health checks
- Docker MySQL config hardened: DB URL built from components via SQLAlchemy `URL.create()` (safe for special chars), backend DB-readiness wait and fail-fast migrations/seed
- GitHub Actions CI for tests, JavaScript syntax and Docker builds
- Final documentation and README
- **Checkpoint 8**

## Post-Launch Backlog
- Two-factor authentication
- S3/R2 storage adapter wiring in the UI
- GitHub contribution heatmap (GraphQL)
- Sinhala/English locale switching
- Predictive engagement analytics with labelled forecasts
- Automated database backup scheduling
