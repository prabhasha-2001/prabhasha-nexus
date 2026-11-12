"""Authentication service: JWT issuance, rotation, password reset."""
from __future__ import annotations

from datetime import timedelta

from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
)

from app.extensions import db
from app.models.base import utcnow
from app.models.user import AdminUser, PasswordResetToken, RefreshToken
from app.utils.errors import ApiError, UnauthorizedError
from app.utils.security import generate_token, token_hash

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15


def _issue_tokens(user: AdminUser, user_agent: str | None = None) -> dict:
    access = create_access_token(
        identity=str(user.id), additional_claims={"role": user.role, "email": user.email}
    )
    refresh = create_refresh_token(
        identity=str(user.id), additional_claims={"role": user.role}
    )
    jti = decode_token(refresh)["jti"]
    expires_at = utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]
    db.session.add(
        RefreshToken(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            user_agent=(user_agent or "")[:255] or None,
        )
    )
    db.session.commit()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "Bearer",
        "expires_in": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
        "user": user.to_dict(),
    }


def authenticate(email: str, password: str, user_agent: str | None = None) -> dict:
    user = AdminUser.query.filter_by(email=(email or "").strip().lower()).first()
    generic = "Invalid email or password"

    if user is None:
        raise UnauthorizedError(generic)

    if not user.is_active:
        raise ApiError("This account is disabled", status_code=403, code="account_disabled")

    if user.is_locked:
        raise ApiError(
            "Account temporarily locked after repeated failed logins",
            status_code=423,
            code="account_locked",
        )

    if not user.check_password(password):
        user.failed_login_count += 1
        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.locked_until = utcnow() + timedelta(minutes=LOCK_MINUTES)
            user.failed_login_count = 0
        db.session.commit()
        raise UnauthorizedError(generic)

    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    db.session.commit()
    return _issue_tokens(user, user_agent)


def rotate_refresh_token(user: AdminUser, user_agent: str | None = None) -> dict:
    claims = get_jwt()
    jti = claims["jti"]
    stored = RefreshToken.query.filter_by(jti=jti).first()
    if stored is None or stored.revoked or stored.expires_at < utcnow():
        raise UnauthorizedError("Refresh token is no longer valid")
    stored.revoked = True
    db.session.commit()
    return _issue_tokens(user, user_agent)


def revoke_refresh_token(jti: str | None = None) -> None:
    jti = jti or get_jwt().get("jti")
    stored = RefreshToken.query.filter_by(jti=jti).first()
    if stored:
        stored.revoked = True
        db.session.commit()


def revoke_all_for_user(user_id: int) -> None:
    RefreshToken.query.filter_by(user_id=user_id, revoked=False).update({"revoked": True})
    db.session.commit()


def change_password(user: AdminUser, current_password: str, new_password: str) -> None:
    if not user.check_password(current_password):
        raise ApiError("Current password is incorrect", status_code=400, code="invalid_password")
    if current_password == new_password:
        raise ApiError("New password must be different", status_code=400, code="validation_error")
    user.set_password(new_password)
    db.session.commit()
    revoke_all_for_user(user.id)


def create_password_reset(email: str) -> tuple[str | None, str]:
    """Return (plain_token_or_none, generic_message). Never reveals account existence."""
    user = AdminUser.query.filter_by(email=(email or "").strip().lower()).first()
    message = "If an account exists for that email, password reset instructions have been generated."
    if user is None:
        return None, message
    token = generate_token()
    db.session.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash(token),
            expires_at=utcnow() + timedelta(minutes=30),
        )
    )
    db.session.commit()
    return token, message


def reset_password(token: str, new_password: str) -> None:
    record = PasswordResetToken.query.filter_by(token_hash=token_hash(token)).first()
    if record is None or record.used or record.expires_at < utcnow():
        raise ApiError("Reset token is invalid or expired", status_code=400, code="invalid_token")
    user = db.session.get(AdminUser, record.user_id)
    if user is None:
        raise ApiError("Reset token is invalid", status_code=400, code="invalid_token")
    user.set_password(new_password)
    record.used = True
    db.session.commit()
    revoke_all_for_user(user.id)
