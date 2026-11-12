# API Documentation — Prabhasha Nexus

Base URL: `http://localhost:5000/api/v1`
Interactive Swagger UI: `http://localhost:5000/api/docs`
OpenAPI JSON: `http://localhost:5000/api/openapi.json`

## Response Envelope

Success:
```json
{ "success": true, "data": {}, "meta": {} }
```
Error:
```json
{ "success": false, "error": { "code": "validation_error", "message": "Request validation failed", "details": {} } }
```

List endpoints return `meta: { page, per_page, total, pages, has_next, has_prev }`.

## Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | public (rate-limited) | Email + password → access & refresh JWT |
| POST | `/auth/refresh` | refresh token | Rotate access token |
| POST | `/auth/logout` | bearer | Revoke refresh token |
| GET | `/auth/me` | bearer | Current admin profile |
| POST | `/auth/change-password` | bearer | Change own password |
| POST | `/auth/forgot-password` | public | Issue reset token (logged, emailed if SMTP) |
| POST | `/auth/reset-password` | public | Consume reset token |

Send `Authorization: Bearer <access_token>`.

Roles: `admin`, `editor`, `viewer`.

## Public Resources (read)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile` | Public profile |
| GET | `/education` | Education timeline |
| GET | `/experience` | Experience/achievements |
| GET | `/achievements` | Achievements |
| GET | `/skills` | Skill categories + skills |
| GET | `/projects` | Paginated projects (`q`, `category`, `type`, `featured`, `sort`, `page`, `per_page`) |
| GET | `/projects/{slug}` | Project detail (+technologies, images, metrics) |
| GET | `/certificates` | Paginated certificates (`q`, `category`, `issuer`, `year`, `featured`) |
| GET | `/certificates/{id}` | Certificate detail |
| GET | `/research` | Research projects |
| GET | `/research/{slug}` | Research detail (+metrics) |
| GET | `/blogs` | Paginated posts (`q`, `category`, `tag`, `featured`) |
| GET | `/blogs/{slug}` | Blog detail (+related) |
| GET | `/testimonials` | Approved testimonials |
| GET | `/resumes` | Active CV versions |
| GET | `/resumes/{id}/download` | Download CV (tracks) |
| GET | `/settings/public` | Public system settings |

## Public Actions

| Method | Path | Description |
|--------|------|-------------|
| POST | `/contact` | Submit contact message (validation + rate limit + honeypot) |
| POST | `/newsletter` | Subscribe (consent required) |
| POST | `/analytics/events` | Track privacy-conscious event |
| POST | `/ai/chat` | AI portfolio assistant (rate-limited) |
| GET | `/ai/suggestions` | Suggested questions |
| GET | `/github/profile` | Cached GitHub profile |
| GET | `/github/repos` | Cached public repositories |
| GET | `/health` | Health check |

## Admin Resources (CRUD)

All require bearer token. Pattern identical for every resource:

```
GET    /admin/{resource}
POST   /admin/{resource}
GET    /admin/{resource}/{id}
PUT    /admin/{resource}/{id}
DELETE /admin/{resource}/{id}
```

Resources: `projects`, `certificates`, `skills`, `skill-categories`, `education`, `experience`, `achievements`, `research`, `blogs`, `blog-categories`, `blog-tags`, `testimonials`, `newsletter`, `resumes`, `media`, `messages`, `users`, `notifications`.

Supporting filters are documented per schema. `viewer` may only `GET`.

## Admin — Dashboard & Analytics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/dashboard` | Real DB KPI summary + recent activity |
| GET | `/analytics/summary?days=30` | Visitors, views, events, series |
| GET | `/analytics/popular` | Popular projects/posts/certificates |
| GET | `/analytics/export.csv` | CSV export of aggregates |
| GET | `/analytics/report` | Printable/summary report payload |

## Admin — Profile & Settings

| Method | Path | Description |
|--------|------|-------------|
| GET/PUT | `/admin/profile` | Update profile |
| GET/PUT | `/admin/settings` | System settings (admin only) |
| GET | `/admin/activity-logs` | Audit trail |
| POST | `/admin/backup` | Create JSON backup |
| GET | `/admin/backup` | List backups |
| GET | `/admin/backup/{filename}` | Download backup |

## AI Intelligence Center

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/ai/conversations` | bearer | List conversations |
| GET | `/admin/ai/conversations/{id}` | bearer | Messages |
| POST | `/admin/ai/content` | editor+ | Generate draft content |
| GET | `/admin/ai/content` | bearer | List generations |
| PATCH | `/admin/ai/content/{id}` | editor+ | Approve/reject draft |
| POST | `/admin/ai/resume/analyze` | editor+ | JD matching against verified profile |
| GET | `/admin/knowledge` | bearer | List documents |
| POST | `/admin/knowledge` | editor+ | Upload PDF (multipart) |
| DELETE | `/admin/knowledge/{id}` | editor+ | Delete doc + chunks |
| POST | `/admin/knowledge/{id}/approve` | editor+ | Approve for public chatbot |
| POST | `/admin/knowledge/rebuild` | editor+ | Rebuild vector index |
| GET | `/admin/knowledge/status` | bearer | Index/processing status |

## Automation & GitHub

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/automation/workflows` | bearer | List workflows |
| POST | `/admin/automation/workflows` | admin | Create workflow |
| PUT | `/admin/automation/workflows/{id}` | admin | Update/enable |
| DELETE | `/admin/automation/workflows/{id}` | admin | Delete |
| POST | `/admin/automation/workflows/{id}/test` | admin | Dispatch test payload |
| GET | `/admin/automation/logs` | bearer | Execution history |
| GET | `/admin/github/repos` | bearer | Repos + cache metadata |
| POST | `/admin/github/refresh` | admin | Invalidate cache |

## Uploads

| Method | Path | Description |
|--------|------|-------------|
| POST | `/admin/media` | Multipart upload (`file`, optional `kind`) |
| GET | `/admin/media` | List media |
| DELETE | `/admin/media/{id}` | Delete media |

Uploads validate magic bytes, extension allowlist, and size. Accepted: images (png/jpeg/webp/svg excluded for safety), PDFs, and CV PDFs. SVG uploads are rejected.

## Error Codes

| HTTP | code | Meaning |
|------|------|---------|
| 400 | `validation_error` | Invalid payload |
| 401 | `unauthorized` / `token_expired` | Missing/expired token |
| 403 | `forbidden` | Insufficient role |
| 404 | `not_found` | Resource missing |
| 409 | `conflict` | Duplicate slug/email |
| 413 | `payload_too_large` | Upload too large |
| 415 | `unsupported_media_type` | Bad upload type |
| 429 | `rate_limited` | Too many requests |
| 500 | `internal_error` | Unhandled server error |

## Rate Limits

Configurable via environment:
- Login: `RATE_LIMIT_LOGIN`
- Contact: `RATE_LIMIT_CONTACT`
- AI: `RATE_LIMIT_AI`
- Default: `RATE_LIMIT_DEFAULT`

## cURL Examples

```bash
# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@prabhashanexus.local","password":"ChangeThisPassword123!"}'

# Public projects
curl "http://localhost:5000/api/v1/projects?page=1&per_page=9&featured=true"

# Contact
curl -X POST http://localhost:5000/api/v1/contact \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane","email":"jane@example.com","subject":"Hello","message":"Interested in your work","website":""}'

# AI chat
curl -X POST http://localhost:5000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What projects has Prabhasha built?","session_id":null}'
```
