"""Automation workflow and execution log models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, iso, utcnow


class AutomationWorkflow(TimestampMixin, db.Model):
    __tablename__ = "automation_workflows"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    event_key = db.Column(db.String(80), nullable=False, index=True)
    webhook_url = db.Column(db.String(600), nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    last_status = db.Column(db.String(30), nullable=True)
    last_run_at = db.Column(db.DateTime, nullable=True)

    logs = db.relationship(
        "AutomationLog", back_populates="workflow",
        cascade="all, delete-orphan", lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "event_key": self.event_key,
            "webhook_url": self.webhook_url,
            "is_enabled": self.is_enabled,
            "last_status": self.last_status,
            "last_run_at": iso(self.last_run_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }


class AutomationLog(db.Model):
    __tablename__ = "automation_logs"

    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(
        db.Integer, db.ForeignKey("automation_workflows.id", ondelete="CASCADE"),
        nullable=True, index=True,
    )
    event_key = db.Column(db.String(80), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, index=True)
    request_payload = db.Column(db.JSON, default=dict)
    response_code = db.Column(db.Integer, nullable=True)
    response_body = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    workflow = db.relationship("AutomationWorkflow", back_populates="logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "event_key": self.event_key,
            "status": self.status,
            "request_payload": self.request_payload or {},
            "response_code": self.response_code,
            "response_body": (self.response_body or "")[:1000] or None,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "created_at": iso(self.created_at),
        }
