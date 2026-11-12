"""Media library and resume management routes."""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, g, request

from app.extensions import db
from app.middleware.audit import log_activity
from app.middleware.auth import auth_required
from app.models import MediaFile, ResumeVersion
from app.schemas import ResumeSchema
from app.utils.errors import ApiError, NotFoundError
from app.utils.pagination import apply_sort, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response
from app.utils.security import save_upload

bp = Blueprint("media", __name__, url_prefix="/admin")

IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
DOCUMENT_EXTENSIONS = {"pdf"}


def _max_bytes() -> int:
    return current_app.config["MAX_CONTENT_LENGTH"]


@bp.post("/media")
@auth_required("editor")
def upload_media():
    file = request.files.get("file")
    kind = request.form.get("kind", "image").lower()
    allowed = DOCUMENT_EXTENSIONS if kind in {"document", "pdf", "resume"} else IMAGE_EXTENSIONS

    saved = save_upload(
        file, base_dir=current_app.config["UPLOAD_DIR"], subdir="media",
        allowed_extensions=allowed, max_bytes=_max_bytes(),
    )
    media = MediaFile(
        filename=saved["filename"],
        original_filename=saved["original_filename"],
        mime_type=_mime_for(saved["extension"]),
        size_bytes=saved["size_bytes"],
        url=saved["url"],
        storage_backend=current_app.config.get("MEDIA_STORAGE_BACKEND", "local"),
        checksum_sha256=saved["checksum_sha256"],
        kind="document" if kind in {"document", "pdf", "resume"} else "image",
        uploaded_by=g.current_user.id,
    )
    db.session.add(media)
    db.session.commit()
    log_activity(g.current_user.id, "media.upload", entity_type="media", entity_id=media.id)
    return success_response(media.to_dict(), status=201)


@bp.get("/media")
@auth_required()
def list_media():
    query = MediaFile.query
    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(MediaFile.original_filename.ilike(f"%{search}%"))
    if request.args.get("kind"):
        query = query.filter(MediaFile.kind == request.args["kind"])
    query = apply_sort(query, MediaFile, default="-created_at")
    page, per_page = parse_pagination(default_per_page=24)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.delete("/media/<int:media_id>")
@auth_required("editor")
def delete_media(media_id):
    media = db.session.get(MediaFile, media_id)
    if media is None:
        raise NotFoundError("Media file not found")
    _delete_local_file(media.url)
    db.session.delete(media)
    db.session.commit()
    log_activity(g.current_user.id, "media.delete", entity_type="media", entity_id=media_id)
    return success_response({"message": "Media deleted"})


@bp.get("/resumes")
@auth_required()
def list_resumes():
    items = ResumeVersion.query.order_by(
        ResumeVersion.is_default.desc(), ResumeVersion.created_at.desc()
    ).all()
    return success_response([item.to_dict() for item in items])


@bp.post("/resumes")
@auth_required("editor")
def create_resume():
    raw = request.form.to_dict()
    payload = ResumeSchema().load(_coerce_bools(raw))
    file = request.files.get("file")
    if file is None:
        raise ApiError("A PDF file is required", status_code=400, code="validation_error")

    saved = save_upload(
        file, base_dir=current_app.config["UPLOAD_DIR"], subdir="resumes",
        allowed_extensions=DOCUMENT_EXTENSIONS, max_bytes=_max_bytes(),
    )
    resume = ResumeVersion(
        label=payload["label"],
        role_family=payload.get("role_family"),
        file_url=saved["url"],
        mime_type="application/pdf",
        size_bytes=saved["size_bytes"],
        is_default=payload.get("is_default", False),
        is_active=payload.get("is_active", True),
        notes=payload.get("notes"),
    )
    db.session.add(resume)
    db.session.flush()
    if resume.is_default:
        ResumeVersion.query.filter(ResumeVersion.id != resume.id).update({"is_default": False})
    db.session.commit()
    log_activity(g.current_user.id, "resume.create", entity_type="resume", entity_id=resume.id)
    return success_response(resume.to_dict(), status=201)


@bp.put("/resumes/<int:resume_id>")
@auth_required("editor")
def update_resume(resume_id):
    resume = db.session.get(ResumeVersion, resume_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    raw = request.get_json(silent=True) or {}
    payload = ResumeSchema().load(raw, partial=True)
    for key, value in payload.items():
        if key in raw:
            setattr(resume, key, value)
    if resume.is_default:
        ResumeVersion.query.filter(ResumeVersion.id != resume.id).update({"is_default": False})
    db.session.commit()
    log_activity(g.current_user.id, "resume.update", entity_type="resume", entity_id=resume.id)
    return success_response(resume.to_dict())


@bp.delete("/resumes/<int:resume_id>")
@auth_required("editor")
def delete_resume(resume_id):
    resume = db.session.get(ResumeVersion, resume_id)
    if resume is None:
        raise NotFoundError("Resume not found")
    _delete_local_file(resume.file_url)
    db.session.delete(resume)
    db.session.commit()
    log_activity(g.current_user.id, "resume.delete", entity_type="resume", entity_id=resume_id)
    return success_response({"message": "Resume deleted"})


def _coerce_bools(data: dict) -> dict:
    result = dict(data)
    for key in ("is_default", "is_active"):
        if key in result:
            result[key] = str(result[key]).lower() in {"1", "true", "yes", "on"}
    return result


def _mime_for(extension: str) -> str:
    return {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "pdf": "application/pdf",
    }.get(extension, "application/octet-stream")


def _delete_local_file(url: str) -> None:
    if not url or not url.startswith("/uploads/"):
        return
    upload_dir = Path(current_app.config["UPLOAD_DIR"]).resolve()
    relative = url.replace("/uploads/", "", 1)
    target = (upload_dir / relative).resolve()
    if upload_dir in target.parents and target.exists():
        target.unlink()
