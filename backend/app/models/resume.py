"""Resume versions and download tracking."""
from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, iso


class ResumeVersion(TimestampMixin, db.Model):
    __tablename__ = "resume_versions"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(150), nullable=False)
    role_family = db.Column(db.String(100), nullable=True, index=True)
    file_url = db.Column(db.String(600), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    is_default = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    download_count = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)

    downloads = db.relationship(
        "ResumeDownload", back_populates="resume", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "role_family": self.role_family,
            "file_url": self.file_url,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "is_default": self.is_default,
            "is_active": self.is_active,
            "download_count": self.download_count,
            "notes": self.notes,
            "created_at": iso(self.created_at),
        }


class ResumeDownload(db.Model):
    __tablename__ = "resume_downloads"

    id = db.Column(db.Integer, primary_key=True)
    resume_id = db.Column(
        db.Integer, db.ForeignKey("resume_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ip_hash = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, index=True)

    resume = db.relationship("ResumeVersion", back_populates="downloads")
