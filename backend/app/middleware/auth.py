"""Authentication and authorization decorators."""
from __future__ import annotations

from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import AdminUser
from app.utils.errors import ForbiddenError, UnauthorizedError

ROLE_HIERARCHY = {"viewer": 1, "editor": 2, "admin": 3}


def _load_user():
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        raise UnauthorizedError("Invalid token identity")
    user = db.session.get(AdminUser, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Account is not available")
    return user


def auth_required(minimum_role: str = "viewer"):
    """Require a valid token whose account meets the minimum role."""

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user = _load_user()
            required = ROLE_HIERARCHY.get(minimum_role, 1)
            actual = ROLE_HIERARCHY.get(user.role, 0)
            if actual < required:
                raise ForbiddenError("Your role does not permit this action")
            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def current_user() -> AdminUser:
    return getattr(g, "current_user", None)
