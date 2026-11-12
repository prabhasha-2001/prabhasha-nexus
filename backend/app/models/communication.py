"""Contact messages, newsletter, testimonials."""
from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, iso

MESSAGE_STATUSES = ("new", "read", "in_progress", "replied", "archived")


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=True)
    subject = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="new", index=True)
    ip_hash = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "subject": self.subject,
            "message": self.message,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "replied_at": iso(self.replied_at),
            "created_at": iso(self.created_at),
        }


class NewsletterSubscriber(TimestampMixin, db.Model):
    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="confirmed", index=True)
    consent_given = db.Column(db.Boolean, nullable=False, default=False)
    consent_at = db.Column(db.DateTime, nullable=True)
    source = db.Column(db.String(100), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "status": self.status,
            "consent_given": self.consent_given,
            "consent_at": iso(self.consent_at),
            "source": self.source,
            "created_at": iso(self.created_at),
        }


class Testimonial(TimestampMixin, db.Model):
    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(150), nullable=False)
    author_role = db.Column(db.String(150), nullable=True)
    organization = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False, index=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author_name": self.author_name,
            "author_role": self.author_role,
            "organization": self.organization,
            "content": self.content,
            "rating": self.rating,
            "avatar_url": self.avatar_url,
            "is_approved": self.is_approved,
            "is_featured": self.is_featured,
            "created_at": iso(self.created_at),
        }
