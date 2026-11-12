"""Academic research models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import SoftDeleteMixin, TimestampMixin, iso


class ResearchProject(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "research_projects"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    abstract = db.Column(db.Text, nullable=True)
    methodology = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    publication_status = db.Column(db.String(100), nullable=True)
    paper_url = db.Column(db.String(500), nullable=True)
    dataset_url = db.Column(db.String(500), nullable=True)
    sample_size = db.Column(db.String(50), nullable=True)
    institutions_count = db.Column(db.String(50), nullable=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text, nullable=True)

    metrics = db.relationship(
        "ResearchMetric", back_populates="research",
        cascade="all, delete-orphan", lazy="selectin", order_by="ResearchMetric.id",
    )

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "abstract": self.abstract,
            "status": self.status,
            "publication_status": self.publication_status,
            "sample_size": self.sample_size,
            "institutions_count": self.institutions_count,
            "is_featured": self.is_featured,
            "created_at": iso(self.created_at),
        }
        if detail:
            data.update(
                {
                    "methodology": self.methodology,
                    "paper_url": self.paper_url,
                    "dataset_url": self.dataset_url,
                    "notes": self.notes,
                    "metrics": [metric.to_dict() for metric in self.metrics],
                }
            )
        return data


class ResearchMetric(db.Model):
    __tablename__ = "research_metrics"

    id = db.Column(db.Integer, primary_key=True)
    research_id = db.Column(
        db.Integer, db.ForeignKey("research_projects.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = db.Column(db.String(200), nullable=False)
    value = db.Column(db.String(100), nullable=False)
    unit = db.Column(db.String(50), nullable=True)
    metric_type = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    research = db.relationship("ResearchProject", back_populates="metrics")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "metric_type": self.metric_type,
            "notes": self.notes,
        }
