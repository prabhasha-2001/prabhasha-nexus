"""API v1 blueprint registration."""
from flask import Blueprint, Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.admin import bp as admin_bp
    from app.routes.analytics import bp as analytics_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.integrations import bp as integrations_bp
    from app.routes.media import bp as media_bp
    from app.routes.public import bp as public_bp
    from app.routes.system import bp as system_bp

    blueprints = [
        auth_bp,
        public_bp,
        analytics_bp,
        admin_bp,
        media_bp,
        integrations_bp,
        system_bp,
    ]

    # AI blueprint is optional during early boot; registered when available.
    try:
        from app.routes.ai import bp as ai_bp

        blueprints.append(ai_bp)
    except ImportError:
        pass

    api = Blueprint("api_v1", __name__, url_prefix="/api/v1")
    for blueprint in blueprints:
        api.register_blueprint(blueprint)
    app.register_blueprint(api)

    from app.routes.docs import bp as docs_bp

    app.register_blueprint(docs_bp)
