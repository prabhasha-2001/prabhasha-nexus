"""Blog models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import SoftDeleteMixin, TimestampMixin, iso

BLOG_STATUSES = ("draft", "published", "archived")

blog_post_tags = db.Table(
    "blog_post_tags",
    db.Column("post_id", db.Integer, db.ForeignKey("blog_posts.id", ondelete="CASCADE"), primary_key=True),
    db.Column("tag_id", db.Integer, db.ForeignKey("blog_tags.id", ondelete="CASCADE"), primary_key=True),
)


class BlogCategory(TimestampMixin, db.Model):
    __tablename__ = "blog_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)

    posts = db.relationship("BlogPost", back_populates="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
        }


class BlogPost(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "blog_posts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False, index=True)
    excerpt = db.Column(db.String(600), nullable=True)
    content = db.Column(db.Text, nullable=False)
    cover_image_url = db.Column(db.String(500), nullable=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("blog_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    featured = db.Column(db.Boolean, nullable=False, default=False, index=True)
    reading_minutes = db.Column(db.Integer, nullable=False, default=1)
    seo_title = db.Column(db.String(300), nullable=True)
    seo_description = db.Column(db.String(400), nullable=True)
    views = db.Column(db.Integer, nullable=False, default=0)
    published_at = db.Column(db.DateTime, nullable=True, index=True)

    category = db.relationship("BlogCategory", back_populates="posts")
    tags = db.relationship(
        "BlogTag", secondary=blog_post_tags, back_populates="posts", lazy="selectin"
    )

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "excerpt": self.excerpt,
            "cover_image_url": self.cover_image_url,
            "category": self.category.to_dict() if self.category else None,
            "tags": [tag.name for tag in self.tags],
            "status": self.status,
            "featured": self.featured,
            "reading_minutes": self.reading_minutes,
            "views": self.views,
            "published_at": iso(self.published_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
        if detail:
            data["content"] = self.content
            data["seo_title"] = self.seo_title
            data["seo_description"] = self.seo_description
        return data


class BlogTag(TimestampMixin, db.Model):
    __tablename__ = "blog_tags"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False, index=True)

    posts = db.relationship("BlogPost", secondary=blog_post_tags, back_populates="tags")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "slug": self.slug}
