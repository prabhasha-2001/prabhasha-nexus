"""Administrators, refresh tokens and password resets."""
from __future__ import annotations

from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.base import TimestampMixin, iso, utcnow

ROLES = ("admin", "editor", "viewer")


class AdminUser(TimestampMixin, db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="editor")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    refresh_tokens = db.relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_locked(self) -> bool:
        return bool(self.locked_until and self.locked_until > utcnow())

    def has_role(self, *roles: str) -> bool:
        return self.role in roles

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "last_login_at": iso(self.last_login_at),
            "created_at": iso(self.created_at),
        }


class RefreshToken(db.Model):
    __tablename__ = "refresh_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    jti = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("AdminUser", back_populates="refresh_tokens")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "jti": self.jti,
            "expires_at": iso(self.expires_at),
            "revoked": self.revoked,
            "created_at": iso(self.created_at),
        }


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = db.Column(db.String(128), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("AdminUser")
