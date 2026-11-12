"""Shared model mixins and helpers."""
from __future__ import annotations

from datetime import datetime, timezone

from app.extensions import db


def utcnow() -> datetime:
    """Naive UTC timestamp (MySQL/SQLite friendly)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class SoftDeleteMixin:
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = utcnow()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None


def iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def iso_date(value) -> str | None:
    return value.isoformat() if value else None
