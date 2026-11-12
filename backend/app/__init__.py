"""Application factory."""
from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from app.config import get_config
from app.extensions import cors, db, jwt, limiter, ma, migrate


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True, static_folder=None)
    app.config.from_object(get_config(config_name))

    _ensure_directories(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    _register_jwt_handlers(app)
    _register_cli(app)
    _configure_logging(app)

    @app.get("/")
    def index():
        return jsonify(
            {
                "success": True,
                "data": {
                    "name": "Prabhasha Nexus API",
                    "version": "1.0.0",
                    "docs": "/api/docs",
                    "health": "/api/v1/health",
                },
            }
        )

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(str(app.config["UPLOAD_DIR"]), filename)

    return app


def _ensure_directories(app: Flask) -> None:
    for key in ("UPLOAD_DIR", "KNOWLEDGE_DIR", "FAISS_INDEX_DIR", "BACKUP_DIR"):
        path = Path(app.config[key])
        path.mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Disposition"],
    )
    limiter.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from app.routes import register_blueprints

    register_blueprints(app)


def _register_error_handlers(app: Flask) -> None:
    from app.utils.errors import register_error_handlers

    register_error_handlers(app)


def _register_security_headers(app: Flask) -> None:
    @app.after_request
    def apply_security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )
        if not app.debug:
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response


def _register_jwt_handlers(app: Flask) -> None:
    from app.utils.responses import error_response

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return error_response("token_expired", "Access token has expired", 401)

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return error_response("unauthorized", "Invalid token", 401)

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response("unauthorized", "Authentication required", 401)

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return error_response("unauthorized", "Token has been revoked", 401)


def _register_cli(app: Flask) -> None:
    from app.services.cli import register_cli

    register_cli(app)


def _configure_logging(app: Flask) -> None:
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
