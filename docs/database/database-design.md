# Database Design — Prabhasha Nexus

Engine: **MySQL 8** (production) / SQLite (local + tests)
ORM: **SQLAlchemy** · Migrations: **Alembic (Flask-Migrate)**

## 1. Conventions

- Primary keys: `id` integer autoincrement (surrogate).
- Slugs are unique where public URLs exist (`projects`, `blog_posts`, `certificate_categories`).
- All content tables carry `created_at` / `updated_at` timestamps.
- Soft deletion via `is_deleted` / `deleted_at` on content and user tables; queries exclude deleted rows by default.
- Enumerated states stored as short strings with validation in schemas.
- Foreign keys use explicit `ondelete` rules; child content cascades where it has no independent meaning.
- Indexes on filter/sort columns: `status`, `featured`, `published_at`, `category_id`, `created_at`.

## 2. Identity & Access

### admin_users
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK | |
| name | VARCHAR(150) | |
| email | VARCHAR(255) UNIQUE | login |
| password_hash | VARCHAR(255) | PBKDF2 |
| role | VARCHAR(20) | admin/editor/viewer |
| is_active | BOOL | |
| last_login_at | DATETIME | |
| failed_login_count | INT | lockout support |
| locked_until | DATETIME | |
| created_at / updated_at | DATETIME | |

### refresh_tokens
`id, user_id FK, jti UNIQUE, expires_at, revoked, created_at`

### password_reset_tokens
`id, user_id FK, token_hash, expires_at, used, created_at`

> Roles/permissions are implemented as a constrained role enum plus per-route guards (RBAC matrix documented in `docs/api`). This avoids an over-normalized permission join for a single-owner platform while remaining extensible.

## 3. Profile & Portfolio Content

### profiles
`id, full_name, professional_title, summary, about, email, phone, location, linkedin_url, github_url, github_username, website_url, avatar_url, resume_url, languages_json, interests_json, career_goals, is_active, created_at, updated_at`

### education
`id, institution, qualification, field_of_study, start_year, end_year, grade, description, location, display_order, is_visible`

### experience
`id, organization, role, employment_type, location, start_date, end_date, is_current, description, achievements_json, display_order, is_visible`

### achievements
`id, title, category, issuer, date, description, url, is_featured, is_visible`

### skill_categories
`id, name UNIQUE, slug UNIQUE, description, display_order`

### skills
`id, category_id FK, name, proficiency INT NULL, icon, display_order, is_featured, is_visible`
> Proficiency shown publicly only when non-null.

### projects
`id, title, slug UNIQUE, short_description, description, problem_statement, solution, architecture, implementation, challenges, future_improvements, dataset_info, status (draft/published/archived), project_type, featured, github_url, live_url, docs_url, thumbnail_url, category_id FK, display_order, views, published_at, created_at, updated_at, is_deleted`

### project_categories
`id, name UNIQUE, slug UNIQUE, description, display_order`

### project_technologies
`id, project_id FK CASCADE, name, display_order`

### project_images
`id, project_id FK CASCADE, media_id FK NULL, url, caption, display_order`

### project_metrics
`id, project_id FK CASCADE, name, value, unit, evaluation_run, notes`
> `evaluation_run` keeps distinct training/validation runs separate (e.g., CNN runs must not be combined).

### certificates
`id, title, issuer, category_id FK NULL, issue_date, expiry_date, credential_id, verification_url, description, image_url, file_url, file_type, featured, status, views, created_at, updated_at, is_deleted`

### certificate_categories
`id, name UNIQUE, slug UNIQUE, description`

### research_projects
`id, title, slug UNIQUE, abstract, methodology, status (draft/published), publication_status, paper_url, dataset_url, sample_size, institutions_count, is_featured, created_at, updated_at`
### research_metrics
`id, research_id FK CASCADE, name, value, unit, metric_type (distribution/model/baseline), notes`

### testimonials
`id, author_name, author_role, organization, content, rating, avatar_url, is_approved, is_featured, created_at`

## 4. Blog

### blog_categories
`id, name UNIQUE, slug UNIQUE, description`
### blog_posts
`id, title, slug UNIQUE, excerpt, content, cover_image_url, category_id FK NULL, status (draft/published/archived), featured, reading_minutes, seo_title, seo_description, views, published_at, created_at, updated_at, is_deleted`
### blog_tags
`id, name UNIQUE, slug UNIQUE`
### blog_post_tags
`post_id FK CASCADE, tag_id FK CASCADE, PK(post_id, tag_id)`

## 5. Media, Communication, Resumes

### media_files
`id, filename, original_filename, mime_type, size_bytes, url, storage_backend, checksum_sha256, uploaded_by FK NULL, created_at`

### contact_messages
`id, name, email, phone, subject, message, status (new/read/in_progress/replied/archived), ip_hash, user_agent, admin_notes, replied_at, created_at, updated_at`

### newsletter_subscribers
`id, email UNIQUE, name, status (pending/confirmed/unsubscribed), consent_given, consent_at, source, created_at`

### resume_versions
`id, label, role_family, file_url, mime_type, size_bytes, is_default, is_active, download_count, notes, created_at, updated_at`

### resume_downloads
`id, resume_id FK CASCADE, ip_hash, user_agent, created_at`

## 6. Analytics (privacy-conscious)

### visitors
`id, visitor_hash UNIQUE, first_seen, last_seen, device_category, source`
### page_views
`id, visitor_hash, path, page_type, content_id NULL, referrer_host, device_category, created_at`
### analytics_events
`id, visitor_hash, event_type (project_view/certificate_view/blog_view/cv_download/github_click/contact_submit/page_view), content_type, content_id, metadata_json, created_at`

> No raw IP addresses stored. Visitor identifiers are salted SHA-256 hashes. No fingerprinting.

## 7. AI

### ai_conversations
`id, session_id UNIQUE, title, channel (public/admin), created_at, updated_at`
### ai_messages
`id, conversation_id FK CASCADE, role (user/assistant/system), content, sources_json, agent, tokens_used, created_at`
### knowledge_documents
`id, title, filename, file_path, mime_type, size_bytes, checksum_sha256, status (pending/processing/indexed/failed), is_approved, chunk_count, error_message, uploaded_by FK NULL, created_at, updated_at`
### knowledge_chunks
`id, document_id FK CASCADE, chunk_index, content, embedding_json, token_estimate`
### ai_generations
`id, kind, prompt, output, status (draft/approved/rejected), provider, model, created_by FK NULL, created_at`

## 8. Automation & System

### automation_workflows
`id, name UNIQUE, slug UNIQUE, description, event_key, webhook_url, is_enabled, last_status, last_run_at, created_at, updated_at`
### automation_logs
`id, workflow_id FK CASCADE, event_key, status (success/failed/not_configured), request_payload_json, response_code, response_body, error_message, duration_ms, created_at`
### notifications
`id, title, message, level (info/success/warning/error), category, is_read, link, created_at`
### admin_activity_logs
`id, user_id FK NULL, action, entity_type, entity_id, metadata_json, ip_hash, created_at`
### system_settings
`id, key UNIQUE, value_json, category, is_public, updated_at`
### scheduled_tasks
`id, name UNIQUE, task_type, schedule, last_run_at, next_run_at, is_enabled, config_json`
### backups
`id, filename, size_bytes, status, created_at`

## 9. Relationship Summary

```
skill_categories 1─* skills
project_categories 1─* projects 1─* project_technologies
                                1─* project_images
                                1─* project_metrics
certificate_categories 1─* certificates
blog_categories 1─* blog_posts *─* blog_tags (blog_post_tags)
research_projects 1─* research_metrics
admin_users 1─* refresh_tokens / ai_generations / media_files
knowledge_documents 1─* knowledge_chunks
automation_workflows 1─* automation_logs
ai_conversations 1─* ai_messages
resume_versions 1─* resume_downloads
```

## 10. Seed Strategy

Seed only verified owner data:
- 1 profile
- 3 education records
- 6 projects + technologies/metrics
- 1 research project + metrics and distributions
- skill categories/skills supported by the verified summary
- an initial administrator from environment variables

**No fake analytics, visitors, certificates, experience, or achievements are seeded.** Certificates remain empty until the owner uploads real ones.

## 11. Migration Strategy

- `flask db init` once (committed), then `flask db migrate -m "..."` and `flask db upgrade` per schema change.
- Production: run `flask db upgrade` as a release step before starting Gunicorn.
- Backups: `flask backup create` exports JSON; MySQL logical dumps handled by hosting provider or `scripts/backup.sh`.
