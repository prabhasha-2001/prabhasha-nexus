"""Project portfolio models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import SoftDeleteMixin, TimestampMixin, iso

PROJECT_STATUSES = ("draft", "published", "archived")


class ProjectCategory(TimestampMixin, db.Model):
    __tablename__ = "project_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    projects = db.relationship("Project", back_populates="category", lazy="dynamic")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "display_order": self.display_order,
        }


class Project(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    short_description = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    problem_statement = db.Column(db.Text, nullable=True)
    solution = db.Column(db.Text, nullable=True)
    architecture = db.Column(db.Text, nullable=True)
    implementation = db.Column(db.Text, nullable=True)
    challenges = db.Column(db.Text, nullable=True)
    future_improvements = db.Column(db.Text, nullable=True)
    dataset_info = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    project_type = db.Column(db.String(80), nullable=True, index=True)
    featured = db.Column(db.Boolean, nullable=False, default=False, index=True)
    github_url = db.Column(db.String(500), nullable=True)
    live_url = db.Column(db.String(500), nullable=True)
    docs_url = db.Column(db.String(500), nullable=True)
    thumbnail_url = db.Column(db.String(500), nullable=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("project_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    display_order = db.Column(db.Integer, nullable=False, default=0)
    views = db.Column(db.Integer, nullable=False, default=0)
    published_at = db.Column(db.DateTime, nullable=True, index=True)

    category = db.relationship("ProjectCategory", back_populates="projects")
    technologies = db.relationship(
        "ProjectTechnology", back_populates="project",
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectTechnology.display_order",
    )
    images = db.relationship(
        "ProjectImage", back_populates="project",
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectImage.display_order",
    )
    metrics = db.relationship(
        "ProjectMetric", back_populates="project",
        cascade="all, delete-orphan", lazy="selectin", order_by="ProjectMetric.id",
    )

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "short_description": self.short_description,
            "status": self.status,
            "project_type": self.project_type,
            "featured": self.featured,
            "github_url": self.github_url,
            "live_url": self.live_url,
            "docs_url": self.docs_url,
            "thumbnail_url": self.thumbnail_url,
            "category": self.category.to_dict() if self.category else None,
            "technologies": [tech.name for tech in self.technologies],
            "display_order": self.display_order,
            "views": self.views,
            "published_at": iso(self.published_at),
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
        if detail:
            data.update(
                {
                    "description": self.description,
                    "problem_statement": self.problem_statement,
                    "solution": self.solution,
                    "architecture": self.architecture,
                    "implementation": self.implementation,
                    "challenges": self.challenges,
                    "future_improvements": self.future_improvements,
                    "dataset_info": self.dataset_info,
                    "images": [image.to_dict() for image in self.images],
                    "metrics": [metric.to_dict() for metric in self.metrics],
                }
            )
        return data


class ProjectTechnology(db.Model):
    __tablename__ = "project_technologies"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    project = db.relationship("Project", back_populates="technologies")

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name}


class ProjectImage(db.Model):
    __tablename__ = "project_images"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_id = db.Column(
        db.Integer, db.ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True
    )
    url = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    project = db.relationship("Project", back_populates="images")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "url": self.url,
            "caption": self.caption,
            "display_order": self.display_order,
        }


class ProjectMetric(db.Model):
    __tablename__ = "project_metrics"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(150), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    evaluation_run = db.Column(db.String(150), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    project = db.relationship("Project", back_populates="metrics")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "evaluation_run": self.evaluation_run,
            "notes": self.notes,
        }
