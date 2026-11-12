"""Admin content request schemas."""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class ProfileSchema(Schema):
    full_name = fields.Str(validate=validate.Length(min=2, max=200))
    professional_title = fields.Str(validate=validate.Length(max=255))
    summary = fields.Str(validate=validate.Length(max=4000))
    about = fields.Str(allow_none=True)
    career_goals = fields.Str(allow_none=True)
    email = fields.Email()
    phone = fields.Str(allow_none=True, validate=validate.Length(max=50))
    location = fields.Str(allow_none=True, validate=validate.Length(max=150))
    linkedin_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    github_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    github_username = fields.Str(allow_none=True, validate=validate.Length(max=150))
    website_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    avatar_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    resume_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    interests = fields.List(fields.Str(), allow_none=True)
    languages = fields.List(fields.Str(), allow_none=True)


class EducationSchema(Schema):
    institution = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    qualification = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    field_of_study = fields.Str(allow_none=True)
    start_year = fields.Str(allow_none=True, validate=validate.Length(max=20))
    end_year = fields.Str(allow_none=True, validate=validate.Length(max=20))
    grade = fields.Str(allow_none=True)
    description = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    display_order = fields.Int(load_default=0)
    is_visible = fields.Bool(load_default=True)


class ExperienceSchema(Schema):
    organization = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    role = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    employment_type = fields.Str(allow_none=True)
    location = fields.Str(allow_none=True)
    start_date = fields.Date(allow_none=True)
    end_date = fields.Date(allow_none=True)
    is_current = fields.Bool(load_default=False)
    description = fields.Str(allow_none=True)
    achievements = fields.List(fields.Str(), allow_none=True)
    display_order = fields.Int(load_default=0)
    is_visible = fields.Bool(load_default=True)


class AchievementSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    category = fields.Str(allow_none=True)
    issuer = fields.Str(allow_none=True)
    date = fields.Date(allow_none=True)
    description = fields.Str(allow_none=True)
    url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    is_featured = fields.Bool(load_default=False)
    is_visible = fields.Bool(load_default=True)


class SkillCategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    description = fields.Str(allow_none=True)
    display_order = fields.Int(load_default=0)


class SkillSchema(Schema):
    category_id = fields.Int(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    proficiency = fields.Int(
        allow_none=True, validate=validate.Range(min=0, max=100)
    )
    icon = fields.Str(allow_none=True)
    display_order = fields.Int(load_default=0)
    is_featured = fields.Bool(load_default=False)
    is_visible = fields.Bool(load_default=True)


class _NamedItemSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    display_order = fields.Int(load_default=0)


class _MetricSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    value = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    unit = fields.Str(allow_none=True)
    evaluation_run = fields.Str(allow_none=True)
    notes = fields.Str(allow_none=True)


class ProjectSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    short_description = fields.Str(
        required=True, validate=validate.Length(min=5, max=500)
    )
    description = fields.Str(allow_none=True)
    problem_statement = fields.Str(allow_none=True)
    solution = fields.Str(allow_none=True)
    architecture = fields.Str(allow_none=True)
    implementation = fields.Str(allow_none=True)
    challenges = fields.Str(allow_none=True)
    future_improvements = fields.Str(allow_none=True)
    dataset_info = fields.Str(allow_none=True)
    status = fields.Str(
        load_default="draft", validate=validate.OneOf(["draft", "published", "archived"])
    )
    project_type = fields.Str(allow_none=True, validate=validate.Length(max=80))
    featured = fields.Bool(load_default=False)
    github_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    live_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    docs_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    thumbnail_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    category_id = fields.Int(allow_none=True)
    display_order = fields.Int(load_default=0)
    technologies = fields.List(fields.Str(), load_default=list)
    images = fields.List(fields.Dict(), load_default=list)
    metrics = fields.List(fields.Nested(_MetricSchema), load_default=list)


class CertificateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    issuer = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    category_id = fields.Int(allow_none=True)
    issue_date = fields.Date(allow_none=True)
    expiry_date = fields.Date(allow_none=True)
    credential_id = fields.Str(allow_none=True)
    verification_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    description = fields.Str(allow_none=True)
    image_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    file_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    file_type = fields.Str(allow_none=True, validate=validate.Length(max=20))
    featured = fields.Bool(load_default=False)
    status = fields.Str(
        load_default="published", validate=validate.OneOf(["draft", "published", "archived"])
    )


class CertificateCategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    description = fields.Str(allow_none=True)


class ResearchSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=5, max=500))
    abstract = fields.Str(allow_none=True)
    methodology = fields.Str(allow_none=True)
    status = fields.Str(
        load_default="draft", validate=validate.OneOf(["draft", "published", "archived"])
    )
    publication_status = fields.Str(allow_none=True)
    paper_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    dataset_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    sample_size = fields.Str(allow_none=True)
    institutions_count = fields.Str(allow_none=True)
    is_featured = fields.Bool(load_default=False)
    notes = fields.Str(allow_none=True)
    metrics = fields.List(fields.Dict(), load_default=list)


class BlogSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=300))
    excerpt = fields.Str(allow_none=True, validate=validate.Length(max=600))
    content = fields.Str(required=True, validate=validate.Length(min=20))
    cover_image_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    category_id = fields.Int(allow_none=True)
    status = fields.Str(
        load_default="draft", validate=validate.OneOf(["draft", "published", "archived"])
    )
    featured = fields.Bool(load_default=False)
    reading_minutes = fields.Int(load_default=1, validate=validate.Range(min=1, max=180))
    seo_title = fields.Str(allow_none=True, validate=validate.Length(max=300))
    seo_description = fields.Str(allow_none=True, validate=validate.Length(max=400))
    tags = fields.List(fields.Str(), load_default=list)


class BlogCategorySchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    description = fields.Str(allow_none=True)


class BlogTagSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))


class TestimonialSchema(Schema):
    author_name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    author_role = fields.Str(allow_none=True)
    organization = fields.Str(allow_none=True)
    content = fields.Str(required=True, validate=validate.Length(min=10, max=2000))
    rating = fields.Int(allow_none=True, validate=validate.Range(min=1, max=5))
    avatar_url = fields.Str(allow_none=True, validate=validate.Length(max=500))
    is_approved = fields.Bool(load_default=False)
    is_featured = fields.Bool(load_default=False)


class ResumeSchema(Schema):
    label = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    role_family = fields.Str(allow_none=True, validate=validate.Length(max=100))
    is_default = fields.Bool(load_default=False)
    is_active = fields.Bool(load_default=True)
    notes = fields.Str(allow_none=True)


class UserSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8, max=200))
    role = fields.Str(
        load_default="editor", validate=validate.OneOf(["admin", "editor", "viewer"])
    )
    is_active = fields.Bool(load_default=True)


class UserUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=2, max=150))
    email = fields.Email()
    password = fields.Str(allow_none=True, validate=validate.Length(min=8, max=200))
    role = fields.Str(validate=validate.OneOf(["admin", "editor", "viewer"]))
    is_active = fields.Bool()


class MessageUpdateSchema(Schema):
    status = fields.Str(
        validate=validate.OneOf(["new", "read", "in_progress", "replied", "archived"])
    )
    admin_notes = fields.Str(allow_none=True)


class WorkflowSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(allow_none=True)
    event_key = fields.Str(required=True, validate=validate.Length(min=2, max=80))
    webhook_url = fields.Str(allow_none=True, validate=validate.Length(max=600))
    is_enabled = fields.Bool(load_default=False)


class NotificationSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    message = fields.Str(required=True, validate=validate.Length(min=2, max=4000))
    level = fields.Str(
        load_default="info", validate=validate.OneOf(["info", "success", "warning", "error"])
    )
    category = fields.Str(allow_none=True)
    link = fields.Str(allow_none=True, validate=validate.Length(max=500))
    is_read = fields.Bool(load_default=False)


class SettingsSchema(Schema):
    settings = fields.Dict(required=True)


class ContentGenerationSchema(Schema):
    kind = fields.Str(
        required=True,
        validate=validate.OneOf(
            [
                "project_description",
                "technical_summary",
                "blog_draft",
                "linkedin_post",
                "certificate_description",
                "portfolio_summary",
                "resume_summary",
            ]
        ),
    )
    prompt = fields.Str(required=True, validate=validate.Length(min=5, max=4000))
    context = fields.Str(load_default="", allow_none=True)


class ResumeAnalyzeSchema(Schema):
    job_description = fields.Str(required=True, validate=validate.Length(min=20, max=8000))
    role_family = fields.Str(load_default=None, allow_none=True)


class GenerationReviewSchema(Schema):
    status = fields.Str(required=True, validate=validate.OneOf(["approved", "rejected"]))


class KnowledgeApproveSchema(Schema):
    is_approved = fields.Bool(load_default=True)
