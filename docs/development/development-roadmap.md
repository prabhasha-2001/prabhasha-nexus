# Development Roadmap — Prabhasha Nexus

Each phase ends with verification, documentation updates, a focused commit, and a push to
`https://github.com/prabhasha-2001/prabhasha-nexus.git`.

Status legend: DONE = implemented and verified; PLANNED = not yet implemented.

## Phase 1 — Foundation [DONE]
- Workspace inspection, Git initialization, remote verification
- Directory structure (frontend/backend/database/docs/docker/scripts)
- `.gitignore`, `.env.example`
- README, architecture, database, API, deployment documentation
- **Checkpoint 1**

## Phase 2 — Database & Backend Foundation [PLANNED]
- Flask application factory, config profiles
- Extensions: SQLAlchemy, Migrate, JWT, CORS, Limiter, Marshmallow
- Models covering identity, portfolio, blog, media, analytics, AI, automation, system
- Alembic migrations + seed command (verified owner data only)
- Centralized error handling, response envelope, health endpoint
- **Checkpoint 2**

## Phase 3 — Core REST APIs [PLANNED]
- Auth: login, refresh, logout, me, change-password, forgot/reset
- Public read APIs for every portfolio resource
- Admin CRUD APIs with RBAC, filtering, sorting, pagination
- Contact, newsletter, media uploads with validation
- Pytest coverage for auth, CRUD, validation, uploads
- **Checkpoint 3**

## Phase 4 — Public Frontend [PLANNED]
- Design system, dark/light theme with persistence
- Home, About, Skills, Projects (+detail), Certificates, Education/Experience,
  Research, Blog (+detail), Contact
- Fetch API integration, loading/empty/error states, AOS animations
- Responsive navigation and accessibility
- **Checkpoint 4**

## Phase 5 — Admin Dashboard [PLANNED]
- JWT login, token refresh, guarded routing
- Dashboard KPIs from real data + charts
- 24 modules with working CRUD, filters, pagination, confirmations, toasts
- **Checkpoint 5**

## Phase 6 — AI Intelligence Center [PLANNED]
- RAG pipeline with PDF upload, extraction, chunking, embeddings, FAISS
- Public chatbot with source-aware, grounded answers
- LangGraph orchestrator with deterministic fallback
- AI content drafts (approval required)
- Resume/JD matching without fabrication
- Mock-based tests
- **Checkpoint 6**

## Phase 7 — Analytics & Integrations [PLANNED]
- Privacy-conscious event tracking and aggregation
- Chart.js dashboards, CSV export, report payload
- GitHub API with caching and rate handling
- n8n webhook automation center with execution logs
- Notification management
- **Checkpoint 7**

## Phase 8 — Testing, Security, Deployment [PLANNED]
- Full Pytest suite (auth, RBAC, CRUD, uploads, analytics, AI mocks, RAG)
- Security hardening: headers, upload magic-byte checks, rate limits, audit logs
- Dockerfile, docker-compose, Nginx, health checks
- GitHub Actions CI
- Final documentation and README
- **Checkpoint 8**

## Post-Launch Backlog
- Two-factor authentication
- S3/R2 storage adapter wiring in UI
- GitHub contribution heatmap (GraphQL)
- Sinhala/English locale switching
- Predictive engagement analytics with labelled forecasts
- Automated DB backup scheduling
