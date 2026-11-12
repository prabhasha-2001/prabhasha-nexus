"""Media library model."""
from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, iso


class MediaFile(TimestampMixin, db.Model):
    __tablename__ = "media_files"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    url = db.Column(db.String(600), nullable=False)
    storage_backend = db.Column(db.String(30), nullable=False, default="local")
    checksum_sha256 = db.Column(db.String(64), nullable=True, index=True)
    kind = db.Column(db.String(30), nullable=False, default="image")
    uploaded_by = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "url": self.url,
            "storage_backend": self.storage_backend,
            "checksum_sha256": self.checksum_sha256,
            "kind": self.kind,
            "created_at": iso(self.created_at),
        }
