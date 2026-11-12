"""Authentication routes."""
from __future__ import annotations

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db, limiter
from app.middleware.auth import auth_required
from app.middleware.audit import log_activity
from app.models.user import AdminUser
from app.schemas import (
    ChangePasswordSchema,
    ForgotPasswordSchema,
    LoginSchema,
    ResetPasswordSchema,
)
from app.services import auth_service
from app.services.email_service import send_email
from app.utils.errors import UnauthorizedError
from app.utils.responses import success_response

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/login")
@limiter.limit(lambda: current_app.config["RATE_LIMIT_LOGIN"])
def login():
    payload = LoginSchema().load(request.get_json(silent=True) or {})
    result = auth_service.authenticate(
        payload["email"], payload["password"], request.user_agent.string
    )
    log_activity(
        result["user"]["id"],
        "auth.login",
        entity_type="admin_user",
        entity_id=result["user"]["id"],
    )
    return success_response(result)


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(AdminUser, int(identity))
    if user is None or not user.is_active:
        raise UnauthorizedError("Account is not available")
    result = auth_service.rotate_refresh_token(user, request.user_agent.string)
    return success_response(result)


@bp.post("/logout")
@jwt_required(refresh=True)
def logout():
    auth_service.revoke_refresh_token(get_jwt().get("jti"))
    return success_response({"message": "Signed out"})


@bp.get("/me")
@auth_required()
def me():
    from flask import g

    return success_response(g.current_user.to_dict())


@bp.post("/change-password")
@auth_required()
def change_password():
    from flask import g

    payload = ChangePasswordSchema().load(request.get_json(silent=True) or {})
    auth_service.change_password(
        g.current_user, payload["current_password"], payload["new_password"]
    )
    log_activity(g.current_user.id, "auth.change_password", entity_type="admin_user",
                 entity_id=g.current_user.id)
    return success_response({"message": "Password updated"})


@bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password():
    payload = ForgotPasswordSchema().load(request.get_json(silent=True) or {})
    token, message = auth_service.create_password_reset(payload["email"])
    if token:
        reset_url = f"{current_app.config['FRONTEND_URL']}/admin/login.html?reset_token={token}"
        send_email(
            payload["email"],
            "Prabhasha Nexus password reset",
            f"Use this link within 30 minutes to reset your password:\n\n{reset_url}\n",
        )
        current_app.logger.info("Password reset token generated for %s", payload["email"])
    data = {"message": message}
    if token and current_app.debug:
        data["dev_reset_token"] = token
    return success_response(data)


@bp.post("/reset-password")
@limiter.limit("10 per hour")
def reset_password():
    payload = ResetPasswordSchema().load(request.get_json(silent=True) or {})
    auth_service.reset_password(payload["token"], payload["new_password"])
    return success_response({"message": "Password has been reset"})
