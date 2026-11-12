"""JSON backup and restore helpers."""
from __future__ import annotations

import json
from pathlib import Path

from flask import current_app

from app.extensions import db
from app.models import (
    Achievement,
    AdminUser,
    BlogCategory,
    BlogPost,
    BlogTag,
    Certificate,
    CertificateCategory,
    ContactMessage,
    Education,
    Experience,
    KnowledgeDocument,
    MediaFile,
    NewsletterSubscriber,
    Profile,
    Project,
    ProjectCategory,
    ResearchProject,
    ResumeVersion,
    Skill,
    SkillCategory,
    SystemSetting,
    Testimonial,
)
from app.models.base import utcnow
from app.models.system import Backup
from app.utils.errors import ApiError

BACKUP_MODELS = [
    AdminUser,
    Profile,
    Education,
    Experience,
    Achievement,
    SkillCategory,
    Skill,
    ProjectCategory,
    Project,
    CertificateCategory,
    Certificate,
    ResearchProject,
    BlogCategory,
    BlogTag,
    BlogPost,
    MediaFile,
    ContactMessage,
    NewsletterSubscriber,
    Testimonial,
    ResumeVersion,
    KnowledgeDocument,
    SystemSetting,
]


def create_backup(label: str | None = None) -> dict:
    backup_dir = Path(current_app.config["BACKUP_DIR"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = utcnow().strftime("%Y%m%d-%H%M%S")
    filename = f"nexus-backup-{label + '-' if label else ''}{timestamp}.json"
    path = backup_dir / filename

    payload = {"generated_at": utcnow().isoformat(), "tables": {}}
    for model in BACKUP_MODELS:
        rows = model.query.all()
        table = model.__tablename__
        if hasattr(model, "to_dict"):
            payload["tables"][table] = [row.to_dict() for row in rows]
        else:
            payload["tables"][table] = [
                {column.name: _serialize(getattr(row, column.name)) for column in model.__table__.columns}
                for row in rows
            ]

    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    record = Backup(
        filename=filename,
        size_bytes=path.stat().st_size,
        status="completed",
    )
    db.session.add(record)
    db.session.commit()
    return record.to_dict()


def list_backups() -> list[dict]:
    backup_dir = Path(current_app.config["BACKUP_DIR"])
    records = Backup.query.order_by(Backup.created_at.desc()).all()
    results = []
    for record in records:
        data = record.to_dict()
        data["exists_on_disk"] = (backup_dir / record.filename).exists()
        results.append(data)
    return results


def backup_path(filename: str) -> Path:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ApiError("Invalid backup filename", status_code=400, code="validation_error")
    path = Path(current_app.config["BACKUP_DIR"]) / filename
    if not path.exists():
        raise ApiError("Backup file not found", status_code=404, code="not_found")
    return path


def _serialize(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
