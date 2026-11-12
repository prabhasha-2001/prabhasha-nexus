"""Administrative audit logging."""
from __future__ import annotations

from flask import has_request_context, request

from app.extensions import db
from app.models.system import AdminActivityLog
from app.utils.security import hash_ip


def log_activity(
    user_id: int | None,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    try:
        ip = request.remote_addr if has_request_context() else ""
        salt = ""
        if has_request_context():
            from flask import current_app

            salt = current_app.config.get("ANALYTICS_SALT", "")
        db.session.add(
            AdminActivityLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata_json=metadata or {},
                ip_hash=hash_ip(ip or "", salt) if salt else None,
            )
        )
        db.session.commit()
    except Exception:  # audit logging must never break the request
        db.session.rollback()
