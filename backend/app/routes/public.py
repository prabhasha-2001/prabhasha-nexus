"""Public portfolio read/action routes."""
from __future__ import annotations

from flask import Blueprint, current_app, request
from sqlalchemy import extract, or_

from app.extensions import db, limiter
from app.models import (
    Achievement,
    BlogCategory,
    BlogPost,
    BlogTag,
    Certificate,
    CertificateCategory,
    ContactMessage,
    Education,
    Experience,
    NewsletterSubscriber,
    Profile,
    Project,
    ProjectCategory,
    ResearchProject,
    ResumeDownload,
    ResumeVersion,
    SkillCategory,
    SystemSetting,
    Testimonial,
)
from app.models.base import utcnow
from app.schemas import ContactSchema, NewsletterSchema
from app.automation import client as automation_client
from app.services import analytics_service, notification_service
from app.utils.errors import ApiError, NotFoundError
from app.utils.pagination import apply_sort, get_bool_arg, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response
from app.utils.security import hash_ip

bp = Blueprint("public", __name__)


# ---------------------------------------------------------------- profile
@bp.get("/profile")
def get_profile():
    profile = Profile.query.filter_by(is_active=True).order_by(Profile.id.asc()).first()
    if profile is None:
        raise NotFoundError("Profile is not available")
    return success_response(profile.to_dict())


@bp.get("/education")
def get_education():
    items = (
        Education.query.filter_by(is_visible=True)
        .order_by(Education.display_order.asc(), Education.end_year.desc())
        .all()
    )
    return success_response([item.to_dict() for item in items])


@bp.get("/experience")
def get_experience():
    items = (
        Experience.query.filter_by(is_visible=True)
        .order_by(Experience.display_order.asc(), Experience.start_date.desc())
        .all()
    )
    return success_response([item.to_dict() for item in items])


@bp.get("/achievements")
def get_achievements():
    items = (
        Achievement.query.filter_by(is_visible=True)
        .order_by(Achievement.is_featured.desc(), Achievement.date.desc())
        .all()
    )
    return success_response([item.to_dict() for item in items])


@bp.get("/skills")
def get_skills():
    categories = SkillCategory.query.order_by(SkillCategory.display_order.asc()).all()
    return success_response([category.to_dict(include_skills=True) for category in categories])


# ---------------------------------------------------------------- projects
@bp.get("/projects")
def list_projects():
    page, per_page = parse_pagination()
    query = Project.query.filter(Project.is_deleted.is_(False), Project.status == "published")
    _apply_project_filters(query)
    query = apply_sort(query, Project, default="-featured,-display_order")

    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Project.title.ilike(like),
                Project.short_description.ilike(like),
                Project.description.ilike(like),
            )
        )

    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([project.to_dict() for project in items], pagination)


def _apply_project_filters(query):
    category = request.args.get("category")
    if category:
        query = query.join(ProjectCategory).filter(ProjectCategory.slug == category)
    project_type = request.args.get("type")
    if project_type:
        query = query.filter(Project.project_type == project_type)
    featured = get_bool_arg("featured")
    if featured is not None:
        query = query.filter(Project.featured.is_(featured))


@bp.get("/projects/categories")
def project_categories():
    items = ProjectCategory.query.order_by(ProjectCategory.display_order.asc()).all()
    return success_response([item.to_dict() for item in items])


@bp.get("/projects/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, is_deleted=False).filter(
        Project.status == "published"
    ).first()
    if project is None:
        raise NotFoundError("Project not found")
    project.views = (project.views or 0) + 1
    db.session.commit()
    return success_response(project.to_dict(detail=True))


# ---------------------------------------------------------------- certificates
@bp.get("/certificates")
def list_certificates():
    page, per_page = parse_pagination()
    query = Certificate.query.filter(
        Certificate.is_deleted.is_(False), Certificate.status == "published"
    )
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(Certificate.title.ilike(like), Certificate.issuer.ilike(like))
        )
    issuer = request.args.get("issuer")
    if issuer:
        query = query.filter(Certificate.issuer == issuer)
    year = request.args.get("year")
    if year:
        if year.isdigit():
            query = query.filter(extract("year", Certificate.issue_date) == int(year))
    category = request.args.get("category")
    if category:
        query = query.join(CertificateCategory).filter(CertificateCategory.slug == category)
    featured = get_bool_arg("featured")
    if featured is not None:
        query = query.filter(Certificate.featured.is_(featured))
    query = apply_sort(query, Certificate, default="-issue_date")
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.get("/certificates/categories")
def certificate_categories():
    items = CertificateCategory.query.order_by(CertificateCategory.name.asc()).all()
    return success_response([item.to_dict() for item in items])


@bp.get("/certificates/<int:certificate_id>")
def certificate_detail(certificate_id):
    certificate = db.session.get(Certificate, certificate_id)
    if certificate is None or certificate.is_deleted or certificate.status != "published":
        raise NotFoundError("Certificate not found")
    certificate.views = (certificate.views or 0) + 1
    db.session.commit()
    return success_response(certificate.to_dict(detail=True))


# ---------------------------------------------------------------- research
@bp.get("/research")
def list_research():
    query = ResearchProject.query.filter(
        ResearchProject.is_deleted.is_(False), ResearchProject.status == "published"
    ).order_by(ResearchProject.is_featured.desc(), ResearchProject.created_at.desc())
    return success_response([item.to_dict() for item in query.all()])


@bp.get("/research/<slug>")
def research_detail(slug):
    research = ResearchProject.query.filter_by(slug=slug, is_deleted=False).first()
    if research is None or research.status != "published":
        raise NotFoundError("Research project not found")
    return success_response(research.to_dict(detail=True))


# ---------------------------------------------------------------- blog
@bp.get("/blogs")
def list_blogs():
    page, per_page = parse_pagination(default_per_page=9)
    query = BlogPost.query.filter(
        BlogPost.is_deleted.is_(False), BlogPost.status == "published"
    )
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(BlogPost.title.ilike(like), BlogPost.excerpt.ilike(like), BlogPost.content.ilike(like))
        )
    category = request.args.get("category")
    if category:
        query = query.join(BlogCategory).filter(BlogCategory.slug == category)
    tag = request.args.get("tag")
    if tag:
        query = query.join(BlogPost.tags).filter(BlogTag.slug == tag)
    featured = get_bool_arg("featured")
    if featured is not None:
        query = query.filter(BlogPost.featured.is_(featured))
    query = apply_sort(query, BlogPost, default="-published_at")
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([post.to_dict() for post in items], pagination)


@bp.get("/blogs/categories")
def blog_categories():
    return success_response(
        [item.to_dict() for item in BlogCategory.query.order_by(BlogCategory.name.asc()).all()]
    )


@bp.get("/blogs/tags")
def blog_tags():
    return success_response(
        [item.to_dict() for item in BlogTag.query.order_by(BlogTag.name.asc()).all()]
    )


@bp.get("/blogs/<slug>")
def blog_detail(slug):
    post = BlogPost.query.filter_by(slug=slug, is_deleted=False).first()
    if post is None or post.status != "published":
        raise NotFoundError("Blog post not found")
    post.views = (post.views or 0) + 1
    related_query = BlogPost.query.filter(
        BlogPost.is_deleted.is_(False),
        BlogPost.status == "published",
        BlogPost.id != post.id,
    )
    if post.category_id:
        related_query = related_query.filter(BlogPost.category_id == post.category_id)
    related = related_query.order_by(BlogPost.published_at.desc()).limit(3).all()
    data = post.to_dict(detail=True)
    data["related"] = [item.to_dict() for item in related]
    db.session.commit()
    return success_response(data)


# ---------------------------------------------------------------- testimonials / resumes
@bp.get("/testimonials")
def list_testimonials():
    items = (
        Testimonial.query.filter_by(is_approved=True)
        .order_by(Testimonial.is_featured.desc(), Testimonial.created_at.desc())
        .all()
    )
    return success_response([item.to_dict() for item in items])


@bp.get("/resumes")
def list_resumes():
    items = (
        ResumeVersion.query.filter_by(is_active=True)
        .order_by(ResumeVersion.is_default.desc(), ResumeVersion.created_at.desc())
        .all()
    )
    return success_response([item.to_dict() for item in items])


@bp.get("/resumes/<int:resume_id>/download")
def download_resume(resume_id):
    resume = db.session.get(ResumeVersion, resume_id)
    if resume is None or not resume.is_active:
        raise NotFoundError("Resume not found")
    resume.download_count = (resume.download_count or 0) + 1
    db.session.add(
        ResumeDownload(
            resume_id=resume.id,
            ip_hash=hash_ip(
                request.remote_addr or "", current_app.config.get("ANALYTICS_SALT", "")
            ),
            user_agent=request.user_agent.string[:500],
            created_at=utcnow(),
        )
    )
    db.session.commit()
    analytics_service.track_event(
        event_type="cv_download",
        content_type="resume",
        content_id=resume.id,
        path=request.path,
    )
    return success_response({"download_url": resume.file_url, "label": resume.label})


# ---------------------------------------------------------------- contact / newsletter
@bp.post("/contact")
@limiter.limit(lambda: current_app.config["RATE_LIMIT_CONTACT"])
def submit_contact():
    payload = ContactSchema().load(request.get_json(silent=True) or {})
    if payload.get("website"):
        # Honeypot triggered: pretend success without persisting.
        return success_response({"message": "Thank you for your message."})

    message = ContactMessage(
        name=payload["name"].strip(),
        email=payload["email"].strip().lower(),
        phone=(payload.get("phone") or None),
        subject=payload["subject"].strip(),
        message=payload["message"].strip(),
        status="new",
        ip_hash=hash_ip(
            request.remote_addr or "", current_app.config.get("ANALYTICS_SALT", "")
        ),
        user_agent=request.user_agent.string[:500],
    )
    db.session.add(message)
    db.session.commit()

    notification_service.create_notification(
        "New contact message",
        f"{message.name} ({message.email}): {message.subject}",
        level="info",
        category="contact",
        link="/admin/index.html#/messages",
    )
    automation_client.dispatch_event(
        "contact.created",
        {
            "id": message.id,
            "name": message.name,
            "email": message.email,
            "subject": message.subject,
        },
    )
    analytics_service.track_event(
        event_type="contact_submit", content_type="contact", content_id=message.id
    )
    return success_response({"message": "Thank you for your message."}, status=201)


@bp.post("/newsletter")
@limiter.limit("10 per hour")
def subscribe_newsletter():
    payload = NewsletterSchema().load(request.get_json(silent=True) or {})
    if not payload.get("consent"):
        raise ApiError(
            "Consent is required to subscribe", status_code=400, code="validation_error"
        )
    email = payload["email"].strip().lower()
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return success_response({"message": "You are already subscribed."})
    subscriber = NewsletterSubscriber(
        email=email,
        name=payload.get("name"),
        status="confirmed",
        consent_given=True,
        consent_at=utcnow(),
        source=payload.get("source") or "website",
    )
    db.session.add(subscriber)
    db.session.commit()
    automation_client.dispatch_event(
        "newsletter.subscribed", {"email": subscriber.email, "id": subscriber.id}
    )
    return success_response({"message": "Subscription confirmed."}, status=201)


# ---------------------------------------------------------------- public settings
@bp.get("/settings/public")
def public_settings():
    settings = SystemSetting.query.filter_by(is_public=True).all()
    return success_response({setting.key: setting.value_json for setting in settings})
