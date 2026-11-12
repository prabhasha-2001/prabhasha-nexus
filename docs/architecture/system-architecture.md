# System Architecture — Prabhasha Nexus

## 1. Overview

Prabhasha Nexus is a modular monolith:

- **Static frontend** (HTML/CSS/vanilla JavaScript) served independently or through Nginx.
- **Flask REST API** (application factory + blueprints) exposing versioned `/api/v1/` endpoints.
- **MySQL** relational database accessed only by the backend through SQLAlchemy.
- **AI layer** (hybrid lexical + optional dense retrieval, optional Groq/OpenRouter LLM) invoked by backend services with deterministic fallbacks.
- **Automation layer** (n8n webhooks) invoked asynchronously with execution logging.

The frontend never talks to the database, AI providers, GitHub, or n8n directly. All sensitive credentials live only in backend environment variables.

## 2. High-Level Diagram

```
┌──────────────────────────┐        HTTPS/JSON        ┌──────────────────────────┐
│  Public Portfolio        │ ───────────────────────▶ │  Flask REST API          │
│  index.html + pages      │                          │  /api/v1/*               │
│  admin/index.html        │ ◀─────────────────────── │  JWT + Rate limiting     │
└──────────────────────────┘                          └───────────┬──────────────┘
                                                                   │
                                                                   │ SQLAlchemy
                                                                   ▼
                                                        ┌──────────────────────────┐
                                                        │  MySQL 8                 │
                                                        │  normalized relational   │
                                                        └──────────────────────────┘
                                                                   │
                          ┌─────────────────────────────────────────┼─────────────────────────┐
                          ▼                                         ▼                         ▼
               ┌────────────────────┐                   ┌────────────────────┐      ┌────────────────────┐
               │ AI Services        │                   │ GitHub Service     │      │ n8n Webhooks       │
               │ lexical + dense    │                   │ cached, rate-aware │      │ authenticated      │
               │ optional LLM       │                   └────────────────────┘      └────────────────────┘
               │ Groq / OpenRouter  │
               └────────────────────┘
```

## 3. Backend Layers

| Layer | Responsibility |
|-------|----------------|
| `routes/` | HTTP concerns only: parse request, call services, return responses |
| `schemas/` | Marshmallow validation/serialization |
| `services/` | Business logic, transactions, orchestration |
| `repositories/` | Reusable query/filter/pagination helpers |
| `models/` | SQLAlchemy ORM entities and relationships |
| `ai/` | Chunking, hybrid retrieval, optional embeddings, LLM client, chat, generation |
| `automation/` | n8n webhook dispatch and logging |
| `middleware/` | Authentication decorators, RBAC, audit, security headers |
| `utils/` | Response envelope, errors, pagination, file validation |

All routes are registered under a single API blueprint tree in `app/routes/__init__.py`, versioned with `v1`.

## 4. Request Lifecycle

1. Request hits Flask after `before_request` hooks (security headers, analytics context).
2. CORS/rate limiter run.
3. JWT is verified for protected routes; role guard applied.
4. Marshmallow schema validates payload.
5. Service executes business logic inside a transaction.
6. Repository builds queries with filtering/sorting/pagination.
7. Response helper returns a consistent envelope:
   ```json
   { "success": true, "data": {...}, "meta": {...} }
   ```
8. Errors are normalized by centralized handlers:
   ```json
   { "success": false, "error": { "code": "validation_error", "message": "...", "details": {...} } }
   ```

## 5. AI Architecture

### 5.1 Retrieval pipeline
1. Admin uploads a PDF/TXT/Markdown document; the file is stored locally under `KNOWLEDGE_DIR` with metadata in the database.
2. Text is extracted (`pypdf` for PDFs), cleaned and chunked with overlap.
3. Each chunk is stored in `knowledge_chunks`; embeddings are optional and stored alongside chunks when enabled.
4. Retrieval combines:
   - lexical scoring with token frequency, IDF and length normalisation
   - cosine similarity over dense embeddings when `sentence-transformers` is installed
   - weighted hybrid score (`0.55` lexical + `0.45` dense) when both are available
5. Top-k chunks plus generated portfolio documents form the grounded context.
6. If no LLM key is configured, a deterministic answer cites retrieved sources without fabricating claims.

There is no external vector database or LangChain/LangGraph runtime; the index is relational and rebuildable with `flask knowledge rebuild`.

### 5.2 Assistant routing
- The assistant uses a single grounded prompt over the retrieved portfolio and knowledge context.
- Domain coverage is achieved through retrieval over profile, projects, skills, research, education, certificates and approved documents.
- Unsupported questions return an explicit "no verified information" response.
- Conversation history is persisted per session with bounded context.

### 5.3 Content & resume assistants
- Drafts are stored with `status=draft`; publishing requires explicit admin action.
- Resume matching compares job-description keywords against verified profile data only; it never invents experience.

## 6. Analytics Architecture

- Lightweight client event tracking (`POST /analytics/events`) with privacy salt hashing of visitor identifiers.
- Server-side aggregation queries produce daily/monthly series, popular content, device categories and traffic sources.
- Predictions (if enabled) are clearly labelled as `prediction` and kept separate from measured values.
- CSV export generated server-side; report payloads are API-driven.

## 7. Security Architecture

- JWT access + refresh tokens; refresh token revocation list in DB.
- RBAC: `admin` (full), `editor` (content CRUD, no user/system management), `viewer` (read-only).
- Rate limits per endpoint class (login, AI, contact, default).
- CORS allowlist from environment.
- Security headers applied globally.
- Uploads validated by magic bytes + extension allowlist + size cap; filenames randomized.
- Admin actions written to `admin_activity_logs`.
- Secrets only in environment; `.env` gitignored.

## 8. Deployment Topology

- Backend: Gunicorn in Docker Compose or on Render/any container host.
- Frontend: Nginx container or static host.
- DB: MySQL 8 in Compose or managed MySQL.
- Media/backups/index: named Docker volume or persistent disk.
- S3-compatible storage: configuration is reserved for a future adapter; the current release uses local disk.

## 9. Design Principles

- Modular monolith over premature microservices.
- Explicit layer boundaries.
- Graceful degradation for every external dependency.
- No hardcoded portfolio data in the frontend.
- Every visible admin action backed by a real endpoint.
- Verified owner data only; AI must never fabricate.
