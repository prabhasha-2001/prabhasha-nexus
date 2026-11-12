"""Profile, education, experience, achievements, skills."""
from __future__ import annotations

from app.extensions import db
from app.models.base import SoftDeleteMixin, TimestampMixin, iso, iso_date


class Profile(TimestampMixin, db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    professional_title = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    about = db.Column(db.Text, nullable=True)
    career_goals = db.Column(db.Text, nullable=True)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    linkedin_url = db.Column(db.String(500), nullable=True)
    github_url = db.Column(db.String(500), nullable=True)
    github_username = db.Column(db.String(150), nullable=True)
    website_url = db.Column(db.String(500), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    resume_url = db.Column(db.String(500), nullable=True)
    interests = db.Column(db.JSON, default=list)
    languages = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "professional_title": self.professional_title,
            "summary": self.summary,
            "about": self.about,
            "career_goals": self.career_goals,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "github_username": self.github_username,
            "website_url": self.website_url,
            "avatar_url": self.avatar_url,
            "resume_url": self.resume_url,
            "interests": self.interests or [],
            "languages": self.languages or [],
            "updated_at": iso(self.updated_at),
        }


class Education(TimestampMixin, db.Model):
    __tablename__ = "education"

    id = db.Column(db.Integer, primary_key=True)
    institution = db.Column(db.String(255), nullable=False)
    qualification = db.Column(db.String(255), nullable=False)
    field_of_study = db.Column(db.String(255), nullable=True)
    start_year = db.Column(db.String(20), nullable=True)
    end_year = db.Column(db.String(20), nullable=True)
    grade = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "institution": self.institution,
            "qualification": self.qualification,
            "field_of_study": self.field_of_study,
            "start_year": self.start_year,
            "end_year": self.end_year,
            "grade": self.grade,
            "description": self.description,
            "location": self.location,
            "display_order": self.display_order,
            "is_visible": self.is_visible,
        }


class Experience(TimestampMixin, db.Model):
    __tablename__ = "experience"

    id = db.Column(db.Integer, primary_key=True)
    organization = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    employment_type = db.Column(db.String(80), nullable=True)
    location = db.Column(db.String(150), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    is_current = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.Text, nullable=True)
    achievements = db.Column(db.JSON, default=list)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization": self.organization,
            "role": self.role,
            "employment_type": self.employment_type,
            "location": self.location,
            "start_date": iso_date(self.start_date),
            "end_date": iso_date(self.end_date),
            "is_current": self.is_current,
            "description": self.description,
            "achievements": self.achievements or [],
            "display_order": self.display_order,
            "is_visible": self.is_visible,
        }


class Achievement(TimestampMixin, db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    issuer = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "issuer": self.issuer,
            "date": iso_date(self.date),
            "description": self.description,
            "url": self.url,
            "is_featured": self.is_featured,
            "is_visible": self.is_visible,
        }


class SkillCategory(TimestampMixin, db.Model):
    __tablename__ = "skill_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    slug = db.Column(db.String(170), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)

    skills = db.relationship(
        "Skill", back_populates="category", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self, include_skills: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "display_order": self.display_order,
        }
        if include_skills:
            data["skills"] = [
                skill.to_dict()
                for skill in self.skills.filter_by(is_visible=True)
                .order_by(Skill.display_order.asc(), Skill.name.asc())
                .all()
            ]
        return data


class Skill(TimestampMixin, db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("skill_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(150), nullable=False)
    proficiency = db.Column(db.Integer, nullable=True)
    icon = db.Column(db.String(100), nullable=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    is_featured = db.Column(db.Boolean, nullable=False, default=False)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)

    category = db.relationship("SkillCategory", back_populates="skills")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "name": self.name,
            "proficiency": self.proficiency,
            "icon": self.icon,
            "display_order": self.display_order,
            "is_featured": self.is_featured,
            "is_visible": self.is_visible,
        }
