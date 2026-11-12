"""OpenAPI specification and Swagger UI."""
from __future__ import annotations

from flask import Blueprint, jsonify

bp = Blueprint("docs", __name__, url_prefix="/api")

_SECURITY = [{"bearerAuth": []}]


def _crud_paths(resource: str, tag: str, item_schema: str | None = None) -> dict:
    return {
        f"/admin/{resource}": {
            "get": {
                "tags": [tag],
                "summary": f"List {resource}",
                "security": _SECURITY,
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "tags": [tag],
                "summary": f"Create {resource}",
                "security": _SECURITY,
                "responses": {"201": {"description": "Created"}},
            },
        },
        f"/admin/{resource}/{{id}}": {
            "get": {
                "tags": [tag],
                "summary": f"Get {resource} item",
                "security": _SECURITY,
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "OK"}},
            },
            "put": {
                "tags": [tag],
                "summary": f"Update {resource} item",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
            "delete": {
                "tags": [tag],
                "summary": f"Delete {resource} item",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
        },
    }


def _build_spec() -> dict:
    paths: dict = {
        "/health": {
            "get": {
                "tags": ["System"],
                "summary": "Health check",
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Login",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"},
                                },
                                "required": ["email", "password"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Tokens issued"},
                    "401": {"description": "Invalid credentials"},
                    "429": {"description": "Rate limited"},
                },
            }
        },
        "/auth/refresh": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Refresh access token",
                "security": [{"refreshBearer": []}],
                "responses": {"200": {"description": "Rotated tokens"}},
            }
        },
        "/auth/me": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Current administrator",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/profile": {
            "get": {"tags": ["Portfolio"], "summary": "Public profile", "responses": {"200": {"description": "OK"}}}
        },
        "/projects": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "List published projects",
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "type", "in": "query", "schema": {"type": "string"}},
                    {"name": "featured", "in": "query", "schema": {"type": "boolean"}},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}},
                    {"name": "page", "in": "query", "schema": {"type": "integer"}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/projects/{slug}": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "Project detail",
                "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}, "404": {"description": "Not found"}},
            }
        },
        "/projects/categories": {
            "get": {"tags": ["Portfolio"], "summary": "Project categories", "responses": {"200": {"description": "OK"}}}
        },
        "/certificates": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "List published certificates",
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "issuer", "in": "query", "schema": {"type": "string"}},
                    {"name": "year", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/certificates/{id}": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "Certificate detail",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/skills": {
            "get": {"tags": ["Portfolio"], "summary": "Skills grouped by category", "responses": {"200": {"description": "OK"}}}
        },
        "/education": {
            "get": {"tags": ["Portfolio"], "summary": "Education timeline", "responses": {"200": {"description": "OK"}}}
        },
        "/experience": {
            "get": {"tags": ["Portfolio"], "summary": "Experience", "responses": {"200": {"description": "OK"}}}
        },
        "/research": {
            "get": {"tags": ["Portfolio"], "summary": "Research projects", "responses": {"200": {"description": "OK"}}}
        },
        "/research/{slug}": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "Research detail",
                "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/blogs": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "List published blog posts",
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "category", "in": "query", "schema": {"type": "string"}},
                    {"name": "tag", "in": "query", "schema": {"type": "string"}},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/blogs/{slug}": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "Blog post detail",
                "parameters": [{"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/testimonials": {
            "get": {"tags": ["Portfolio"], "summary": "Approved testimonials", "responses": {"200": {"description": "OK"}}}
        },
        "/resumes": {
            "get": {"tags": ["Portfolio"], "summary": "Active resume versions", "responses": {"200": {"description": "OK"}}}
        },
        "/resumes/{id}/download": {
            "get": {
                "tags": ["Portfolio"],
                "summary": "Download CV (tracked)",
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/contact": {
            "post": {
                "tags": ["Communication"],
                "summary": "Submit contact message",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "email": {"type": "string", "format": "email"},
                                    "phone": {"type": "string"},
                                    "subject": {"type": "string"},
                                    "message": {"type": "string"},
                                    "website": {"type": "string", "description": "Honeypot; must be empty"},
                                },
                                "required": ["name", "email", "subject", "message"],
                            }
                        }
                    },
                },
                "responses": {"201": {"description": "Created"}, "429": {"description": "Rate limited"}},
            }
        },
        "/newsletter": {
            "post": {
                "tags": ["Communication"],
                "summary": "Subscribe to newsletter (consent required)",
                "responses": {"201": {"description": "Created"}},
            }
        },
        "/analytics/events": {
            "post": {
                "tags": ["Analytics"],
                "summary": "Track a privacy-conscious analytics event",
                "responses": {"202": {"description": "Accepted"}},
            }
        },
        "/admin/dashboard": {
            "get": {
                "tags": ["Admin"],
                "summary": "Dashboard KPIs and charts",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/analytics/summary": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Analytics summary",
                "security": _SECURITY,
                "parameters": [{"name": "days", "in": "query", "schema": {"type": "integer"}}],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/analytics/export.csv": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Export analytics CSV",
                "security": _SECURITY,
                "responses": {"200": {"description": "CSV file"}},
            }
        },
        "/analytics/report": {
            "get": {
                "tags": ["Analytics"],
                "summary": "Summary report payload",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/github/profile": {
            "get": {"tags": ["GitHub"], "summary": "Cached GitHub profile", "responses": {"200": {"description": "OK"}}}
        },
        "/github/repos": {
            "get": {"tags": ["GitHub"], "summary": "Cached GitHub repositories", "responses": {"200": {"description": "OK"}}}
        },
        "/admin/github/refresh": {
            "post": {
                "tags": ["GitHub"],
                "summary": "Clear GitHub cache",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/admin/automation/workflows": {
            "get": {
                "tags": ["Automation"],
                "summary": "List workflows",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "tags": ["Automation"],
                "summary": "Create workflow",
                "security": _SECURITY,
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/admin/automation/logs": {
            "get": {
                "tags": ["Automation"],
                "summary": "Execution history",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/admin/settings": {
            "get": {
                "tags": ["System"],
                "summary": "List settings",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
            "put": {
                "tags": ["System"],
                "summary": "Update settings",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
        },
        "/admin/backups": {
            "get": {
                "tags": ["System"],
                "summary": "List backups",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "tags": ["System"],
                "summary": "Create backup",
                "security": _SECURITY,
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/admin/activity-logs": {
            "get": {
                "tags": ["System"],
                "summary": "Audit trail",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/ai/chat": {
            "post": {
                "tags": ["AI"],
                "summary": "AI portfolio assistant",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "session_id": {"type": "string", "nullable": True},
                                },
                                "required": ["message"],
                            }
                        }
                    },
                },
                "responses": {"200": {"description": "Grounded answer"}, "429": {"description": "Rate limited"}},
            }
        },
        "/ai/suggestions": {
            "get": {"tags": ["AI"], "summary": "Suggested questions", "responses": {"200": {"description": "OK"}}}
        },
        "/admin/knowledge": {
            "get": {
                "tags": ["AI"],
                "summary": "List knowledge documents",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "tags": ["AI"],
                "summary": "Upload knowledge PDF",
                "security": _SECURITY,
                "responses": {"201": {"description": "Created"}},
            },
        },
        "/admin/ai/content": {
            "post": {
                "tags": ["AI"],
                "summary": "Generate draft content",
                "security": _SECURITY,
                "responses": {"201": {"description": "Draft created"}},
            }
        },
        "/admin/ai/resume/analyze": {
            "post": {
                "tags": ["AI"],
                "summary": "Match job description against verified profile",
                "security": _SECURITY,
                "responses": {"200": {"description": "OK"}},
            }
        },
    }

    for resource, tag in [
        ("projects", "Projects"),
        ("certificates", "Certificates"),
        ("education", "Education"),
        ("experience", "Experience"),
        ("achievements", "Achievements"),
        ("skills", "Skills"),
        ("skill-categories", "Skills"),
        ("project-categories", "Projects"),
        ("certificate-categories", "Certificates"),
        ("blogs", "Blog"),
        ("blog-categories", "Blog"),
        ("blog-tags", "Blog"),
        ("research", "Research"),
        ("testimonials", "Testimonials"),
        ("messages", "Communication"),
        ("newsletter", "Communication"),
        ("media", "Media"),
        ("resumes", "Resumes"),
        ("users", "Users"),
        ("notifications", "Notifications"),
    ]:
        for path, methods in _crud_paths(resource, tag).items():
            existing = paths.setdefault(path, {})
            for method, operation in methods.items():
                existing.setdefault(method, operation)

    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Prabhasha Nexus API",
            "version": "1.0.0",
            "description": (
                "AI-Powered Personal Portfolio & Intelligence Management Platform API. "
                "All admin routes require a JWT bearer token. Public routes are rate-limited."
            ),
        },
        "servers": [{"url": "/api/v1", "description": "Versioned API"}],
        "tags": [
            {"name": "Authentication"},
            {"name": "Portfolio"},
            {"name": "Projects"},
            {"name": "Certificates"},
            {"name": "Blog"},
            {"name": "Research"},
            {"name": "Communication"},
            {"name": "Analytics"},
            {"name": "GitHub"},
            {"name": "Automation"},
            {"name": "AI"},
            {"name": "Admin"},
            {"name": "System"},
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                "refreshBearer": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT refresh"},
            }
        },
        "paths": paths,
    }


@bp.get("/openapi.json")
def openapi():
    return jsonify(_build_spec())


@bp.get("/docs")
def swagger_ui():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prabhasha Nexus API Docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
  <style>body{margin:0;background:#0b1020} .topbar{display:none}</style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({
      url: '/api/openapi.json',
      dom_id: '#swagger-ui',
      deepLinking: true,
      presets: [SwaggerUIBundle.presets.apis],
      layout: 'BaseLayout'
    });
  </script>
</body>
</html>"""
