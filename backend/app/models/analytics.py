"""Privacy-conscious analytics models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import iso, utcnow

EVENT_TYPES = (
    "page_view",
    "project_view",
    "certificate_view",
    "blog_view",
    "cv_download",
    "github_click",
    "contact_submit",
)


class Visitor(db.Model):
    __tablename__ = "visitors"

    id = db.Column(db.Integer, primary_key=True)
    visitor_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    first_seen = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_seen = db.Column(db.DateTime, nullable=False, default=utcnow)
    device_category = db.Column(db.String(30), nullable=True)
    source = db.Column(db.String(120), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "visitor_hash": self.visitor_hash[:12],
            "first_seen": iso(self.first_seen),
            "last_seen": iso(self.last_seen),
            "device_category": self.device_category,
            "source": self.source,
        }


class PageView(db.Model):
    __tablename__ = "page_views"

    id = db.Column(db.Integer, primary_key=True)
    visitor_hash = db.Column(db.String(64), nullable=False, index=True)
    path = db.Column(db.String(500), nullable=False, index=True)
    page_type = db.Column(db.String(50), nullable=False, default="page", index=True)
    content_id = db.Column(db.Integer, nullable=True)
    referrer_host = db.Column(db.String(200), nullable=True)
    device_category = db.Column(db.String(30), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "path": self.path,
            "page_type": self.page_type,
            "content_id": self.content_id,
            "referrer_host": self.referrer_host,
            "device_category": self.device_category,
            "created_at": iso(self.created_at),
        }


class AnalyticsEvent(db.Model):
    __tablename__ = "analytics_events"

    id = db.Column(db.Integer, primary_key=True)
    visitor_hash = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    content_type = db.Column(db.String(50), nullable=True)
    content_id = db.Column(db.Integer, nullable=True)
    metadata_json = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "content_type": self.content_type,
            "content_id": self.content_id,
            "metadata": self.metadata_json or {},
            "created_at": iso(self.created_at),
        }
