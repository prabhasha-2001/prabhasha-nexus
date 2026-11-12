"""Admin CRUD routes for portfolio content and management modules."""
from __future__ import annotations

from flask import Blueprint, g, request
from sqlalchemy import or_

from app.extensions import db
from app.middleware.audit import log_activity
from app.middleware.auth import auth_required
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
    NewsletterSubscriber,
    Notification,
    Profile,
    Project,
    ProjectCategory,
    ProjectImage,
    ProjectMetric,
    ProjectTechnology,
    ResearchMetric,
    ResearchProject,
    Skill,
    SkillCategory,
    Testimonial,
)
from app.models.base import utcnow
from app.schemas import (
    AchievementSchema,
    BlogCategorySchema,
    BlogSchema,
    BlogTagSchema,
    CertificateCategorySchema,
    CertificateSchema,
    EducationSchema,
    ExperienceSchema,
    MessageUpdateSchema,
    NotificationSchema,
    ProfileSchema,
    ProjectSchema,
    ResearchSchema,
    SkillCategorySchema,
    SkillSchema,
    TestimonialSchema,
    UserSchema,
    UserUpdateSchema,
)
from app.automation import client as automation_client
from app.services import admin_crud, notification_service
from app.services.admin_crud import ResourceConfig
from app.utils.errors import ApiError, ConflictError, NotFoundError
from app.utils.pagination import apply_sort, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response
from app.utils.security import unique_slug

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ================================================================ profile
@bp.get("/profile")
@auth_required()
def get_profile():
    profile = Profile.query.order_by(Profile.id.asc()).first()
    if profile is None:
        raise NotFoundError("Profile not found")
    return success_response(profile.to_dict())


@bp.put("/profile")
@auth_required("editor")
def update_profile():
    profile = Profile.query.order_by(Profile.id.asc()).first()
    if profile is None:
        profile = Profile(
            full_name="", professional_title="", summary="", email=""
        )
        db.session.add(profile)
        db.session.flush()
    raw = request.get_json(silent=True) or {}
    payload = ProfileSchema().load(raw, partial=True)
    for key, value in payload.items():
        if key in raw:
            setattr(profile, key, value)
    db.session.commit()
    log_activity(g.current_user.id, "profile.update", entity_type="profile", entity_id=profile.id)
    return success_response(profile.to_dict())


# ================================================================ projects
@bp.get("/projects")
@auth_required()
def list_projects():
    query = Project.query.filter(Project.is_deleted.is_(False))
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(Project.title.ilike(like), Project.short_description.ilike(like)))
    for param, attr in (("status", "status"), ("category_id", "category_id"),
                        ("project_type", "project_type")):
        value = request.args.get(param)
        if value not in (None, ""):
            query = query.filter(getattr(Project, attr) == value)
    featured = request.args.get("featured")
    if featured in ("true", "false"):
        query = query.filter(Project.featured.is_(featured == "true"))
    query = apply_sort(query, Project, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([project.to_dict() for project in items], pagination)


@bp.post("/projects")
@auth_required("editor")
def create_project():
    payload = ProjectSchema().load(request.get_json(silent=True) or {})
    project = Project(
        title=payload["title"],
        slug=unique_slug(Project, payload["title"]),
        short_description=payload["short_description"],
    )
    _apply_project_scalars(project, payload)
    if project.status == "published" and project.published_at is None:
        project.published_at = utcnow()
    _apply_project_children(project, payload)
    db.session.add(project)
    db.session.commit()
    log_activity(g.current_user.id, "project.create", entity_type="project", entity_id=project.id)
    notification_service.create_notification(
        "Project created", project.title, level="success", category="projects",
        link=f"/admin/index.html#/projects",
    )
    if project.status == "published":
        automation_client.dispatch_event("project.created", {"id": project.id, "title": project.title})
    return success_response(project.to_dict(detail=True), status=201)


@bp.get("/projects/<int:project_id>")
@auth_required()
def get_project(project_id):
    project = _project_or_404(project_id)
    return success_response(project.to_dict(detail=True))


@bp.get("/projects/<int:project_id>/preview")
@auth_required()
def preview_project(project_id):
    project = _project_or_404(project_id)
    return success_response(project.to_dict(detail=True))


@bp.put("/projects/<int:project_id>")
@auth_required("editor")
def update_project(project_id):
    project = _project_or_404(project_id)
    previous_status = project.status
    raw = request.get_json(silent=True) or {}
    loaded = ProjectSchema().load(raw, partial=True)
    payload = {key: value for key, value in loaded.items() if key in raw}
    if payload.get("title") and payload["title"] != project.title:
        project.slug = unique_slug(Project, payload["title"], current_id=project.id)
    _apply_project_scalars(project, payload)
    if project.status == "published" and project.published_at is None:
        project.published_at = utcnow()
    payload_with_children = dict(payload)
    _apply_project_children(project, payload_with_children)
    db.session.commit()
    log_activity(g.current_user.id, "project.update", entity_type="project", entity_id=project.id)
    if project.status == "published" and previous_status != "published":
        automation_client.dispatch_event("project.created", {"id": project.id, "title": project.title})
    return success_response(project.to_dict(detail=True))


@bp.delete("/projects/<int:project_id>")
@auth_required("editor")
def delete_project(project_id):
    project = _project_or_404(project_id)
    project.soft_delete()
    db.session.commit()
    log_activity(g.current_user.id, "project.delete", entity_type="project", entity_id=project.id)
    return success_response({"message": "Project deleted"})


def _project_or_404(project_id: int) -> Project:
    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if project is None:
        raise NotFoundError("Project not found")
    return project


def _apply_project_scalars(project: Project, payload: dict) -> None:
    scalar_fields = {
        "short_description", "description", "problem_statement", "solution", "architecture",
        "implementation", "challenges", "future_improvements", "dataset_info", "status",
        "project_type", "featured", "github_url", "live_url", "docs_url", "thumbnail_url",
        "category_id", "display_order",
    }
    for key in scalar_fields:
        if key in payload:
            setattr(project, key, payload[key])


def _apply_project_children(project: Project, payload: dict) -> None:
    if "technologies" in payload:
        project.technologies = [
            ProjectTechnology(name=name.strip(), display_order=index)
            for index, name in enumerate(payload["technologies"], start=1)
            if str(name).strip()
        ]
    if "images" in payload:
        images = []
        for index, image in enumerate(payload["images"], start=1):
            url = (image or {}).get("url", "").strip()
            if not url:
                continue
            images.append(
                ProjectImage(
                    url=url,
                    caption=(image.get("caption") or "")[:255] or None,
                    display_order=image.get("display_order", index),
                )
            )
        project.images = images
    if "metrics" in payload:
        project.metrics = [
            ProjectMetric(
                name=metric["name"],
                value=str(metric["value"]),
                unit=metric.get("unit"),
                evaluation_run=metric.get("evaluation_run"),
                notes=metric.get("notes"),
            )
            for metric in payload["metrics"]
        ]


# ================================================================ certificates (generic)
def _certificate_after_create(certificate: Certificate):
    notification_service.create_notification(
        "Certificate added", certificate.title, level="info", category="certificates",
        link="/admin/index.html#/certificates",
    )
    automation_client.dispatch_event(
        "certificate.created", {"id": certificate.id, "title": certificate.title}
    )


# ================================================================ blogs
@bp.get("/blogs")
@auth_required()
def list_blogs():
    query = BlogPost.query.filter(BlogPost.is_deleted.is_(False))
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(or_(BlogPost.title.ilike(like), BlogPost.excerpt.ilike(like)))
    for param, attr in (("status", "status"), ("category_id", "category_id")):
        value = request.args.get(param)
        if value not in (None, ""):
            query = query.filter(getattr(BlogPost, attr) == value)
    if request.args.get("featured") in ("true", "false"):
        query = query.filter(BlogPost.featured.is_(request.args["featured"] == "true"))
    query = apply_sort(query, BlogPost, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([post.to_dict() for post in items], pagination)


@bp.post("/blogs")
@auth_required("editor")
def create_blog():
    raw = request.get_json(silent=True) or {}
    payload = BlogSchema().load(raw)
    post = BlogPost(
        title=payload["title"],
        slug=unique_slug(BlogPost, payload["title"]),
        excerpt=payload.get("excerpt"),
        content=payload["content"],
    )
    _apply_blog_scalars(post, payload)
    post.reading_minutes = payload.get("reading_minutes") or _reading_minutes(payload["content"])
    post.tags = _resolve_tags(payload.get("tags") or [])
    if post.status == "published" and post.published_at is None:
        post.published_at = utcnow()
    db.session.add(post)
    db.session.commit()
    log_activity(g.current_user.id, "blog.create", entity_type="blog_post", entity_id=post.id)
    notification_service.create_notification(
        "Blog post created", post.title, level="success", category="blog",
        link="/admin/index.html#/blog",
    )
    if post.status == "published":
        automation_client.dispatch_event("blog.published", {"id": post.id, "title": post.title})
    return success_response(post.to_dict(detail=True), status=201)


@bp.get("/blogs/<int:post_id>")
@auth_required()
def get_blog(post_id):
    post = _blog_or_404(post_id)
    return success_response(post.to_dict(detail=True))


@bp.put("/blogs/<int:post_id>")
@auth_required("editor")
def update_blog(post_id):
    post = _blog_or_404(post_id)
    previous_status = post.status
    raw = request.get_json(silent=True) or {}
    loaded = BlogSchema().load(raw, partial=True)
    payload = {key: value for key, value in loaded.items() if key in raw}
    if payload.get("title") and payload["title"] != post.title:
        post.slug = unique_slug(BlogPost, payload["title"], current_id=post.id)
    _apply_blog_scalars(post, payload)
    if "content" in payload and "reading_minutes" not in raw:
        post.reading_minutes = _reading_minutes(payload["content"])
    if "tags" in payload:
        post.tags = _resolve_tags(payload["tags"] or [])
    if post.status == "published" and post.published_at is None:
        post.published_at = utcnow()
    db.session.commit()
    log_activity(g.current_user.id, "blog.update", entity_type="blog_post", entity_id=post.id)
    if post.status == "published" and previous_status != "published":
        automation_client.dispatch_event("blog.published", {"id": post.id, "title": post.title})
    return success_response(post.to_dict(detail=True))


@bp.delete("/blogs/<int:post_id>")
@auth_required("editor")
def delete_blog(post_id):
    post = _blog_or_404(post_id)
    post.soft_delete()
    db.session.commit()
    log_activity(g.current_user.id, "blog.delete", entity_type="blog_post", entity_id=post.id)
    return success_response({"message": "Blog post deleted"})


def _blog_or_404(post_id: int) -> BlogPost:
    post = BlogPost.query.filter_by(id=post_id, is_deleted=False).first()
    if post is None:
        raise NotFoundError("Blog post not found")
    return post


def _apply_blog_scalars(post: BlogPost, payload: dict) -> None:
    for key in (
        "excerpt", "content", "cover_image_url", "category_id", "status", "featured",
        "reading_minutes", "seo_title", "seo_description",
    ):
        if key in payload:
            setattr(post, key, payload[key])


def _reading_minutes(content: str) -> int:
    words = len((content or "").split())
    return max(1, round(words / 200))


def _resolve_tags(names: list[str]) -> list[BlogTag]:
    tags = []
    for name in names:
        clean = (name or "").strip()
        if not clean:
            continue
        tag = BlogTag.query.filter(db.func.lower(BlogTag.name) == clean.lower()).first()
        if tag is None:
            tag = BlogTag(name=clean, slug=unique_slug(BlogTag, clean))
            db.session.add(tag)
            db.session.flush()
        tags.append(tag)
    return tags


# ================================================================ research
@bp.get("/research")
@auth_required()
def list_research():
    query = ResearchProject.query.filter(ResearchProject.is_deleted.is_(False))
    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(ResearchProject.title.ilike(f"%{search}%"))
    if request.args.get("status"):
        query = query.filter(ResearchProject.status == request.args["status"])
    query = apply_sort(query, ResearchProject, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.post("/research")
@auth_required("editor")
def create_research():
    payload = ResearchSchema().load(request.get_json(silent=True) or {})
    research = ResearchProject(
        title=payload["title"], slug=unique_slug(ResearchProject, payload["title"])
    )
    _apply_research_scalars(research, payload)
    if "metrics" in payload:
        research.metrics = _research_metrics(payload["metrics"])
    db.session.add(research)
    db.session.commit()
    log_activity(g.current_user.id, "research.create", entity_type="research", entity_id=research.id)
    return success_response(research.to_dict(detail=True), status=201)


@bp.get("/research/<int:research_id>")
@auth_required()
def get_research(research_id):
    return success_response(_research_or_404(research_id).to_dict(detail=True))


@bp.put("/research/<int:research_id>")
@auth_required("editor")
def update_research(research_id):
    research = _research_or_404(research_id)
    raw = request.get_json(silent=True) or {}
    loaded = ResearchSchema().load(raw, partial=True)
    payload = {key: value for key, value in loaded.items() if key in raw}
    if payload.get("title") and payload["title"] != research.title:
        research.slug = unique_slug(ResearchProject, payload["title"], current_id=research.id)
    _apply_research_scalars(research, payload)
    if "metrics" in payload:
        research.metrics = _research_metrics(payload["metrics"])
    db.session.commit()
    log_activity(g.current_user.id, "research.update", entity_type="research", entity_id=research.id)
    return success_response(research.to_dict(detail=True))


@bp.delete("/research/<int:research_id>")
@auth_required("editor")
def delete_research(research_id):
    research = _research_or_404(research_id)
    research.soft_delete()
    db.session.commit()
    log_activity(g.current_user.id, "research.delete", entity_type="research", entity_id=research.id)
    return success_response({"message": "Research deleted"})


def _research_or_404(research_id: int) -> ResearchProject:
    research = ResearchProject.query.filter_by(id=research_id, is_deleted=False).first()
    if research is None:
        raise NotFoundError("Research record not found")
    return research


def _apply_research_scalars(research: ResearchProject, payload: dict) -> None:
    for key in (
        "abstract", "methodology", "status", "publication_status", "paper_url", "dataset_url",
        "sample_size", "institutions_count", "is_featured", "notes",
    ):
        if key in payload:
            setattr(research, key, payload[key])


def _research_metrics(items: list[dict]) -> list[ResearchMetric]:
    return [
        ResearchMetric(
            name=item["name"],
            value=str(item["value"]),
            unit=item.get("unit"),
            metric_type=item.get("metric_type"),
            notes=item.get("notes"),
        )
        for item in items
    ]


# ================================================================ messages
@bp.get("/messages")
@auth_required()
def list_messages():
    query = ContactMessage.query
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                ContactMessage.name.ilike(like),
                ContactMessage.email.ilike(like),
                ContactMessage.subject.ilike(like),
                ContactMessage.message.ilike(like),
            )
        )
    if request.args.get("status"):
        query = query.filter(ContactMessage.status == request.args["status"])
    query = apply_sort(query, ContactMessage, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.get("/messages/<int:message_id>")
@auth_required()
def get_message(message_id):
    message = db.session.get(ContactMessage, message_id)
    if message is None:
        raise NotFoundError("Message not found")
    return success_response(message.to_dict())


@bp.put("/messages/<int:message_id>")
@auth_required()
def update_message(message_id):
    message = db.session.get(ContactMessage, message_id)
    if message is None:
        raise NotFoundError("Message not found")
    payload = MessageUpdateSchema().load(request.get_json(silent=True) or {}, partial=True)
    if "status" in payload:
        message.status = payload["status"]
        if payload["status"] == "replied":
            message.replied_at = utcnow()
    if "admin_notes" in payload:
        message.admin_notes = payload["admin_notes"]
    db.session.commit()
    log_activity(g.current_user.id, "message.update", entity_type="contact_message",
                 entity_id=message.id)
    return success_response(message.to_dict())


@bp.delete("/messages/<int:message_id>")
@auth_required("editor")
def delete_message(message_id):
    message = db.session.get(ContactMessage, message_id)
    if message is None:
        raise NotFoundError("Message not found")
    db.session.delete(message)
    db.session.commit()
    log_activity(g.current_user.id, "message.delete", entity_type="contact_message",
                 entity_id=message_id)
    return success_response({"message": "Message deleted"})


# ================================================================ newsletter
@bp.get("/newsletter")
@auth_required()
def list_newsletter():
    query = NewsletterSubscriber.query
    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(NewsletterSubscriber.email.ilike(f"%{search}%"))
    if request.args.get("status"):
        query = query.filter(NewsletterSubscriber.status == request.args["status"])
    query = apply_sort(query, NewsletterSubscriber, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.put("/newsletter/<int:subscriber_id>")
@auth_required("editor")
def update_newsletter(subscriber_id):
    subscriber = db.session.get(NewsletterSubscriber, subscriber_id)
    if subscriber is None:
        raise NotFoundError("Subscriber not found")
    payload = request.get_json(silent=True) or {}
    if payload.get("status") in {"pending", "confirmed", "unsubscribed"}:
        subscriber.status = payload["status"]
    db.session.commit()
    log_activity(g.current_user.id, "newsletter.update", entity_type="newsletter",
                 entity_id=subscriber.id)
    return success_response(subscriber.to_dict())


@bp.delete("/newsletter/<int:subscriber_id>")
@auth_required("editor")
def delete_newsletter(subscriber_id):
    subscriber = db.session.get(NewsletterSubscriber, subscriber_id)
    if subscriber is None:
        raise NotFoundError("Subscriber not found")
    db.session.delete(subscriber)
    db.session.commit()
    log_activity(g.current_user.id, "newsletter.delete", entity_type="newsletter",
                 entity_id=subscriber_id)
    return success_response({"message": "Subscriber removed"})


# ================================================================ users
@bp.get("/users")
@auth_required("admin")
def list_users():
    users = AdminUser.query.order_by(AdminUser.created_at.asc()).all()
    return success_response([user.to_dict() for user in users])


@bp.post("/users")
@auth_required("admin")
def create_user():
    payload = UserSchema().load(request.get_json(silent=True) or {})
    email = payload["email"].strip().lower()
    if AdminUser.query.filter_by(email=email).first():
        raise ConflictError("An account with that email already exists")
    user = AdminUser(
        name=payload["name"], email=email, role=payload["role"],
        is_active=payload.get("is_active", True),
    )
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()
    log_activity(g.current_user.id, "user.create", entity_type="admin_user", entity_id=user.id)
    return success_response(user.to_dict(), status=201)


@bp.put("/users/<int:user_id>")
@auth_required("admin")
def update_user(user_id):
    user = db.session.get(AdminUser, user_id)
    if user is None:
        raise NotFoundError("User not found")
    payload = UserUpdateSchema().load(request.get_json(silent=True) or {}, partial=True)
    if payload.get("email"):
        email = payload["email"].strip().lower()
        existing = AdminUser.query.filter(AdminUser.email == email, AdminUser.id != user.id).first()
        if existing:
            raise ConflictError("An account with that email already exists")
        user.email = email
    for key in ("name", "role", "is_active"):
        if key in payload:
            setattr(user, key, payload[key])
    if payload.get("password"):
        user.set_password(payload["password"])
    db.session.commit()
    log_activity(g.current_user.id, "user.update", entity_type="admin_user", entity_id=user.id)
    return success_response(user.to_dict())


@bp.delete("/users/<int:user_id>")
@auth_required("admin")
def delete_user(user_id):
    user = db.session.get(AdminUser, user_id)
    if user is None:
        raise NotFoundError("User not found")
    if user.id == g.current_user.id:
        raise ApiError("You cannot delete your own account", status_code=400,
                       code="validation_error")
    if user.role == "admin" and AdminUser.query.filter_by(role="admin").count() <= 1:
        raise ApiError("At least one administrator must remain", status_code=400,
                       code="validation_error")
    db.session.delete(user)
    db.session.commit()
    log_activity(g.current_user.id, "user.delete", entity_type="admin_user", entity_id=user_id)
    return success_response({"message": "User deleted"})


# ================================================================ generic resources
def _register_generic(resource: str, config: ResourceConfig, *, write_role: str = "editor"):
    config.resource = resource

    def list_view():
        return admin_crud.list_items(config)

    def create_view():
        return admin_crud.create_item(config)

    def detail_view(item_id):
        return success_response(admin_crud.get_item(config, item_id))

    def update_view(item_id):
        return admin_crud.update_item(config, item_id)

    def delete_view(item_id):
        return admin_crud.delete_item(config, item_id)

    bp.add_url_rule(f"/{resource}", f"{resource}_list", auth_required()(list_view), methods=["GET"])
    if config.allow_create:
        bp.add_url_rule(
            f"/{resource}", f"{resource}_create",
            auth_required(write_role)(create_view), methods=["POST"],
        )
    bp.add_url_rule(
        f"/{resource}/<int:item_id>", f"{resource}_detail",
        auth_required()(detail_view), methods=["GET"],
    )
    if config.allow_update:
        bp.add_url_rule(
            f"/{resource}/<int:item_id>", f"{resource}_update",
            auth_required(write_role)(update_view), methods=["PUT"],
        )
    if config.allow_delete:
        bp.add_url_rule(
            f"/{resource}/<int:item_id>", f"{resource}_delete",
            auth_required(write_role)(delete_view), methods=["DELETE"],
        )


_register_generic("education", ResourceConfig(
    model=Education, schema=EducationSchema,
    search_fields=["institution", "qualification"],
    filter_map={"visible": "is_visible"},
    default_sort="display_order", entity_type="education",
))
_register_generic("experience", ResourceConfig(
    model=Experience, schema=ExperienceSchema,
    search_fields=["organization", "role"],
    filter_map={"visible": "is_visible"},
    default_sort="display_order", entity_type="experience",
))
_register_generic("achievements", ResourceConfig(
    model=Achievement, schema=AchievementSchema,
    search_fields=["title", "issuer", "category"],
    filter_map={"featured": "is_featured", "visible": "is_visible"},
    default_sort="-date", entity_type="achievement",
))
_register_generic("skill-categories", ResourceConfig(
    model=SkillCategory, schema=SkillCategorySchema,
    search_fields=["name"], slug_source="name",
    default_sort="display_order", entity_type="skill_category",
))
_register_generic("skills", ResourceConfig(
    model=Skill, schema=SkillSchema,
    search_fields=["name"], filter_map={"category_id": "category_id", "visible": "is_visible"},
    default_sort="display_order", entity_type="skill",
))
_register_generic("project-categories", ResourceConfig(
    model=ProjectCategory, schema=SkillCategorySchema,
    search_fields=["name"], slug_source="name",
    default_sort="display_order", entity_type="project_category",
))
_register_generic("certificate-categories", ResourceConfig(
    model=CertificateCategory, schema=CertificateCategorySchema,
    search_fields=["name"], slug_source="name",
    default_sort="name", entity_type="certificate_category",
))
_register_generic("certificates", ResourceConfig(
    model=Certificate, schema=CertificateSchema, soft_delete=True,
    search_fields=["title", "issuer"], slug_source=None,
    filter_map={"status": "status", "featured": "featured", "category_id": "category_id"},
    default_sort="-issue_date", entity_type="certificate",
    after_create=_certificate_after_create,
))
_register_generic("blog-categories", ResourceConfig(
    model=BlogCategory, schema=BlogCategorySchema,
    search_fields=["name"], slug_source="name",
    default_sort="name", entity_type="blog_category",
))
_register_generic("blog-tags", ResourceConfig(
    model=BlogTag, schema=BlogTagSchema,
    search_fields=["name"], slug_source="name",
    default_sort="name", entity_type="blog_tag",
))
_register_generic("testimonials", ResourceConfig(
    model=Testimonial, schema=TestimonialSchema,
    search_fields=["author_name", "organization"],
    filter_map={"approved": "is_approved", "featured": "is_featured"},
    default_sort="-created_at", entity_type="testimonial",
))
_register_generic("notifications", ResourceConfig(
    model=Notification, schema=NotificationSchema,
    search_fields=["title", "message"],
    filter_map={"read": "is_read", "level": "level"},
    default_sort="-created_at", entity_type="notification",
))
