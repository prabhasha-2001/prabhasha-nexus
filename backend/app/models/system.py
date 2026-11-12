"""System models: notifications, audit logs, settings, tasks, backups."""
from __future__ import annotations

from app.extensions import db
from app.models.base import iso, utcnow


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), nullable=False, default="info")
    category = db.Column(db.String(60), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    link = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "level": self.level,
            "category": self.category,
            "is_read": self.is_read,
            "link": self.link,
            "created_at": iso(self.created_at),
        }


class AdminActivityLog(db.Model):
    __tablename__ = "admin_activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(60), nullable=True, index=True)
    entity_id = db.Column(db.Integer, nullable=True)
    metadata_json = db.Column(db.JSON, default=dict)
    ip_hash = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    user = db.relationship("AdminUser")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "metadata": self.metadata_json or {},
            "created_at": iso(self.created_at),
        }


class SystemSetting(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False, index=True)
    value_json = db.Column(db.JSON, nullable=True)
    category = db.Column(db.String(60), nullable=False, default="general")
    is_public = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value_json,
            "category": self.category,
            "is_public": self.is_public,
            "updated_at": iso(self.updated_at),
        }


class ScheduledTask(db.Model):
    __tablename__ = "scheduled_tasks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    task_type = db.Column(db.String(80), nullable=False)
    schedule = db.Column(db.String(80), nullable=True)
    last_run_at = db.Column(db.DateTime, nullable=True)
    next_run_at = db.Column(db.DateTime, nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    config_json = db.Column(db.JSON, default=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "task_type": self.task_type,
            "schedule": self.schedule,
            "last_run_at": iso(self.last_run_at),
            "next_run_at": iso(self.next_run_at),
            "is_enabled": self.is_enabled,
            "config": self.config_json or {},
        }


class Backup(db.Model):
    __tablename__ = "backups"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="completed")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "created_at": iso(self.created_at),
        }
