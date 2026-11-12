"""Notification creation and dispatch."""
from __future__ import annotations

from app.extensions import db
from app.models.system import Notification


def create_notification(
    title: str,
    message: str,
    *,
    level: str = "info",
    category: str | None = None,
    link: str | None = None,
) -> Notification:
    notification = Notification(
        title=title, message=message, level=level, category=category, link=link
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def unread_count() -> int:
    return Notification.query.filter_by(is_read=False).count()
