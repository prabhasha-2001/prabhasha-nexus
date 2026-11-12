# System Architecture — Prabhasha Nexus

## 1. Overview

Prabhasha Nexus is a modular monolith:

- **Static frontend** (HTML/CSS/JS) served independently or via Nginx.
- **Flask REST API** (application factory + blueprints) exposing versioned `/api/v1/` endpoints.
- **MySQL** relational database accessed only by the backend through SQLAlchemy.
- **AI layer** (LangChain / LangGraph / FAISS) invoked by backend services with deterministic fallbacks.
- **Automation layer** (n8n webhooks) invoked asynchronously (fire-and-forget with logging).

The frontend never talks to the database, AI providers, GitHub, or n8n directly. All sensitive credentials live only in backend environment variables.

## 2. High-Level Diagram

```
┌──────────────────────────┐        HTTPS/JSON        ┌──────────────────────────┐
│  Public Portfolio (SPA-  │ ───────────────────────▶ │  Flask REST API          │
│  style static pages)     │                          │  /api/v1/*               │
│  index.html + pages/*    │ ◀─────────────────────── │  JWT + Rate limiting     │
└──────────────────────────┘                          └───────────┬──────────────┘
                                                                   │
┌──────────────────────────┐                                       │ SQLAlchemy
│  Admin Dashboard         │ ──────────────────────────────────────┤
│  /admin (JWT protected)  │                                       │
└──────────────────────────┘                                       ▼
                                                       ┌──────────────────────────┐
                                                       │  MySQL 8                 │
                                                       │  normalized relational   │
                                                       └──────────────────────────┘
                                                                   │
                         ┌─────────────────────────────────────────┼─────────────────────────┐
                         ▼                                         ▼                         ▼
              ┌────────────────────┐                   ┌────────────────────┐      ┌────────────────────┐
              │ AI Services        │                   │ GitHub Service     │      │ n8n Webhooks       │
              │ RAG / FAISS        │                   │ cached, rate-aware │      │ authenticated      │
              │ LangGraph agents   │                   └────────────────────┘      └────────────────────┘
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
| `ai/` | Embeddings, vector store, RAG pipeline, LangGraph, LLM client |
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

### 5.1 RAG pipeline
1. Admin uploads PDF → stored under persistent upload path (configurable S3 adapter).
2. Text extracted → cleaned → chunked (overlapping windows).
3. Embeddings generated:
   - `sentence-transformers` + FAISS when installed/available.
   - Deterministic hashing embeddings + numpy cosine similarity fallback otherwise.
4. Index persisted with document metadata.
5. Query → embed → top-k retrieval → grounded prompt → LLM.
6. If no LLM key: answer is composed from retrieved context with source citations (no fabrication).

### 5.2 LangGraph multi-agent routing
- Orchestrator classifies intent: `profile | projects | skills | career | research | certificates | contact | general`.
- Node handlers retrieve domain-specific context from the database and knowledge base.
- A verification node rejects unsupported claims and enforces "I don't have that information" behaviour.
- Error/retry wrapper with bounded retries and structured logging.
- When LangGraph is not installed, an equivalent deterministic router executes the same nodes.

### 5.3 Content & resume assistants
- Drafts are stored with `status=draft`; publishing requires explicit admin action.
- Resume matching compares job description keywords against verified profile data only; it never invents experience.

## 6. Analytics Architecture

- Lightweight client event tracking (`POST /analytics/events`) with privacy salt hashing of visitor identifiers.
- Server-side aggregation queries produce daily/monthly series, popular content, device categories, and traffic sources.
- Predictions (if enabled) are clearly labelled as `prediction` and kept separate from measured values.
- CSV export generated server-side; PDF report uses a minimal built-in generator or printable view.

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

- Backend: Gunicorn behind Render/any container host.
- Frontend: static host or Nginx container.
- DB: managed MySQL (Render MySQL, PlanetScale, RDS).
- Media: persistent disk or S3-compatible bucket (recommended).
- Vector index: persistent disk or rebuildable from DB metadata + stored documents.

## 9. Design Principles

- Modular monolith over premature microservices.
- Explicit layer boundaries.
- Graceful degradation for every external dependency.
- No hardcoded portfolio data in the frontend.
- Every visible admin action backed by a real endpoint.
- Verified owner data only; AI must never fabricate.
