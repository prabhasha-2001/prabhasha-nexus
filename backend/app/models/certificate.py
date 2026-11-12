"""Certificate models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import SoftDeleteMixin, TimestampMixin, iso, iso_date


class CertificateCategory(TimestampMixin, db.Model):
    __tablename__ = "certificate_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    certificates = db.relationship("Certificate", back_populates="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
        }


class Certificate(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "certificates"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    issuer = db.Column(db.String(255), nullable=False, index=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("certificate_categories.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    issue_date = db.Column(db.Date, nullable=True, index=True)
    expiry_date = db.Column(db.Date, nullable=True)
    credential_id = db.Column(db.String(255), nullable=True)
    verification_url = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    file_url = db.Column(db.String(500), nullable=True)
    file_type = db.Column(db.String(20), nullable=True)
    featured = db.Column(db.Boolean, nullable=False, default=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="published", index=True)
    views = db.Column(db.Integer, nullable=False, default=0)

    category = db.relationship("CertificateCategory", back_populates="certificates")

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "issuer": self.issuer,
            "category": self.category.to_dict() if self.category else None,
            "issue_date": iso_date(self.issue_date),
            "expiry_date": iso_date(self.expiry_date),
            "credential_id": self.credential_id,
            "verification_url": self.verification_url,
            "description": self.description,
            "image_url": self.image_url,
            "file_url": self.file_url,
            "file_type": self.file_type,
            "featured": self.featured,
            "status": self.status,
            "views": self.views,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
        if detail:
            data["verification_note"] = (
                "Credential verification has not been performed by the platform. "
                "Follow the issuer's verification link."
            )
        return data
