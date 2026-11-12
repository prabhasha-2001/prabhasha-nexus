"""AI chatbot, knowledge base and content-generation routes."""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from flask import Blueprint, current_app, g, request
from werkzeug.utils import secure_filename

from app.ai import content_generator, llm
from app.ai.chat_service import answer_chat, conversation_detail, list_conversations
from app.ai.embeddings import backend_name
from app.ai.rag_service import index_document, rebuild_index
from app.extensions import db, limiter
from app.middleware.audit import log_activity
from app.middleware.auth import auth_required
from app.models import AIConversation, AIGeneration, KnowledgeDocument
from app.schemas import (
    ChatSchema,
    ContentGenerationSchema,
    GenerationReviewSchema,
    KnowledgeApproveSchema,
    ResumeAnalyzeSchema,
)
from app.utils.errors import ApiError, NotFoundError
from app.utils.pagination import Pagination, apply_sort, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response

bp = Blueprint("ai", __name__)

ALLOWED_KNOWLEDGE_EXTENSIONS = {"pdf", "txt", "md", "markdown"}
MIME_TYPES = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "markdown": "text/markdown",
}


@bp.get("/ai/status")
def ai_status():
    documents = KnowledgeDocument.query.all()
    return success_response(
        {
            "llm_configured": llm.is_configured(),
            "llm_provider": (llm.resolve_provider() or ("none",))[0],
            "retrieval_backend": backend_name(),
            "knowledge_documents": len(documents),
            "approved_documents": sum(1 for item in documents if item.is_approved),
            "indexed_chunks": sum(item.chunk_count for item in documents),
            "behavior": "Answers are grounded in verified portfolio content; no unverifiable claims.",
        }
    )


@bp.post("/ai/chat")
@limiter.limit(lambda: current_app.config["RATE_LIMIT_AI"])
def chat():
    payload = ChatSchema().load(request.get_json(silent=True) or {})
    result = answer_chat(payload["message"], payload.get("session_id"), channel="public")
    return success_response(result)


@bp.get("/admin/ai/conversations")
@auth_required()
def conversations():
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = list_conversations(page, per_page)
    return paginated_response(
        items,
        Pagination(page=page, per_page=per_page, total=pagination.total),
    )


@bp.get("/admin/ai/conversations/<int:conversation_id>")
@auth_required()
def get_conversation(conversation_id):
    data = conversation_detail(conversation_id)
    if not data:
        raise NotFoundError("Conversation not found")
    return success_response(data)


@bp.get("/admin/ai/knowledge")
@auth_required()
def list_knowledge():
    query = KnowledgeDocument.query
    search = request.args.get("q", "").strip()
    if search:
        query = query.filter(KnowledgeDocument.title.ilike(f"%{search}%"))
    if request.args.get("status"):
        query = query.filter(KnowledgeDocument.status == request.args["status"])
    if request.args.get("approved") in {"true", "false"}:
        query = query.filter(
            KnowledgeDocument.is_approved.is_(request.args["approved"] == "true")
        )
    query = apply_sort(query, KnowledgeDocument, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.post("/admin/ai/knowledge")
@auth_required("editor")
def upload_knowledge():
    file = request.files.get("file")
    if file is None or not file.filename:
        raise ApiError("A document file is required", status_code=400, code="validation_error")
    filename = secure_filename(file.filename)
    if "." not in filename:
        raise ApiError("File has no extension", status_code=415, code="unsupported_media_type")
    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_KNOWLEDGE_EXTENSIONS:
        raise ApiError(
            "Only PDF, Markdown and text documents are supported",
            status_code=415,
            code="unsupported_media_type",
            details={"allowed": sorted(ALLOWED_KNOWLEDGE_EXTENSIONS)},
        )

    directory = Path(current_app.config["UPLOAD_DIR"]) / "knowledge"
    directory.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex[:10]}-{filename}"
    path = directory / stored_name
    file.save(path)
    size = path.stat().st_size
    if size == 0:
        path.unlink(missing_ok=True)
        raise ApiError("The uploaded document is empty", status_code=400, code="validation_error")
    if size > current_app.config["MAX_CONTENT_LENGTH"]:
        path.unlink(missing_ok=True)
        raise ApiError("Document exceeds the upload limit", status_code=413, code="payload_too_large")

    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    document = KnowledgeDocument(
        title=(request.form.get("title") or Path(filename).stem)[:300],
        filename=stored_name,
        file_path=str(path),
        mime_type=MIME_TYPES.get(extension, "application/octet-stream"),
        size_bytes=size,
        checksum_sha256=checksum,
        status="pending",
        is_approved=False,
        uploaded_by=g.current_user.id,
    )
    db.session.add(document)
    db.session.commit()
    document = index_document(document)
    log_activity(
        g.current_user.id, "ai.knowledge.upload", entity_type="knowledge_document",
        entity_id=document.id,
    )
    return success_response(document.to_dict(), status=201)


@bp.post("/admin/ai/knowledge/<int:document_id>/approve")
@auth_required("admin")
def approve_knowledge(document_id):
    document = db.session.get(KnowledgeDocument, document_id)
    if document is None:
        raise NotFoundError("Knowledge document not found")
    payload = KnowledgeApproveSchema().load(request.get_json(silent=True) or {})
    document.is_approved = payload["is_approved"]
    db.session.commit()
    log_activity(
        g.current_user.id, "ai.knowledge.approve", entity_type="knowledge_document",
        entity_id=document.id, metadata={"approved": document.is_approved},
    )
    return success_response(document.to_dict())


@bp.delete("/admin/ai/knowledge/<int:document_id>")
@auth_required("editor")
def delete_knowledge(document_id):
    document = db.session.get(KnowledgeDocument, document_id)
    if document is None:
        raise NotFoundError("Knowledge document not found")
    _delete_file(document.file_path)
    db.session.delete(document)
    db.session.commit()
    log_activity(
        g.current_user.id, "ai.knowledge.delete", entity_type="knowledge_document",
        entity_id=document_id,
    )
    return success_response({"message": "Knowledge document deleted"})


@bp.post("/admin/ai/knowledge/rebuild")
@auth_required("admin")
def rebuild_knowledge():
    result = rebuild_index()
    log_activity(g.current_user.id, "ai.knowledge.rebuild", entity_type="knowledge_document")
    return success_response(result)


@bp.post("/admin/ai/generate")
@auth_required("editor")
def generate():
    payload = ContentGenerationSchema().load(request.get_json(silent=True) or {})
    record = content_generator.generate_content(
        payload["kind"], payload["prompt"], payload.get("context") or "", g.current_user.id
    )
    log_activity(g.current_user.id, "ai.generate", entity_type="ai_generation", entity_id=record["id"],
                 metadata={"kind": record["kind"]})
    return success_response(record, status=201)


@bp.get("/admin/ai/generations")
@auth_required()
def list_generations():
    query = AIGeneration.query
    if request.args.get("kind"):
        query = query.filter(AIGeneration.kind == request.args["kind"])
    if request.args.get("status"):
        query = query.filter(AIGeneration.status == request.args["status"])
    query = apply_sort(query, AIGeneration, default="-created_at")
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.put("/admin/ai/generations/<int:generation_id>/review")
@auth_required("editor")
def review_generation(generation_id):
    payload = GenerationReviewSchema().load(request.get_json(silent=True) or {})
    record = content_generator.review_generation(generation_id, payload["status"])
    if not record:
        raise NotFoundError("Generation not found")
    log_activity(
        g.current_user.id, "ai.generation.review", entity_type="ai_generation",
        entity_id=generation_id, metadata={"status": payload["status"]},
    )
    return success_response(record)


@bp.post("/admin/ai/resume/analyze")
@auth_required("editor")
def analyze_resume():
    payload = ResumeAnalyzeSchema().load(request.get_json(silent=True) or {})
    result = content_generator.analyze_resume(
        payload["job_description"], payload.get("role_family"), g.current_user.id
    )
    log_activity(g.current_user.id, "ai.resume.analyze", entity_type="ai_generation",
                 entity_id=result["id"])
    return success_response(result, status=201)


def _delete_file(file_path: str) -> None:
    if not file_path:
        return
    path = Path(file_path)
    upload_dir = Path(current_app.config["UPLOAD_DIR"]).resolve()
    try:
        target = path.resolve()
    except OSError:
        return
    if upload_dir in target.parents and target.exists():
        target.unlink(missing_ok=True)
