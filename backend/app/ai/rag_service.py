"""AI retrieval, indexing and chatbot services."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from flask import current_app

from app.ai.embeddings import backend_name, cosine_similarity, embed_texts
from app.extensions import db
from app.models import (
    BlogPost,
    Certificate,
    Education,
    KnowledgeChunk,
    KnowledgeDocument,
    Profile,
    Project,
    ResearchProject,
    Skill,
    SkillCategory,
    Testimonial,
)

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "what", "when", "where", "who",
    "how", "why", "are", "was", "were", "has", "have", "had", "does", "did", "can", "could",
    "would", "should", "about", "into", "your", "you", "their", "them", "they", "his", "her",
    "she", "him", "its", "our", "out", "not", "but", "all", "any", "may", "also", "than",
    "then", "there", "these", "those", "will", "just", "more", "most", "some", "such", "very",
    "tell", "give", "please", "show", "know", "want", "work", "worked", "working",
}

CHUNK_SIZE = 900
CHUNK_OVERLAP = 120


def _tokens(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9][a-z0-9+#.]*", (text or "").lower())
        if len(token) > 1 and token not in STOPWORDS
    ]


def extract_text(path: str | Path, mime_type: str | None = None) -> str:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".pdf" or (mime_type or "").endswith("pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as exc:  # pragma: no cover - dependency is in requirements
            raise RuntimeError("pypdf is required to read PDF documents") from exc
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    normalized = re.sub(r"\r\n?", "\n", text or "").strip()
    if not normalized:
        return []
    paragraphs = [part.strip() for part in re.split(r"\n{2,}", normalized) if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= size:
            current = f"{current}\n\n{paragraph}".strip()
            continue
        if current:
            chunks.append(current)
        if len(paragraph) <= size:
            current = paragraph
        else:
            start = 0
            while start < len(paragraph):
                piece = paragraph[start:start + size]
                chunks.append(piece)
                start += size - overlap
            current = ""
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if len(chunk) >= 20]


def _portfolio_documents() -> list[dict]:
    documents: list[dict] = []
    profile = Profile.query.order_by(Profile.id.asc()).first()
    if profile:
        content = "\n".join(
            filter(
                None,
                [
                    f"Name: {profile.full_name}",
                    f"Professional title: {profile.professional_title}",
                    f"Summary: {profile.summary}",
                    f"About: {profile.about or ''}",
                    f"Career goals: {profile.career_goals or ''}",
                    f"Location: {profile.location or ''}",
                    f"Email: {profile.email}",
                    f"Interests: {', '.join(profile.interests or [])}",
                    f"Languages: {', '.join(profile.languages or [])}",
                    f"LinkedIn: {profile.linkedin_url or ''}",
                    f"GitHub: {profile.github_url or ''}",
                ],
            )
        )
        documents.append({"title": "Professional profile", "source": "/#about", "content": content})

    education = Education.query.filter_by(is_visible=True).order_by(Education.display_order).all()
    if education:
        lines = [
            f"{item.qualification} at {item.institution} ({item.start_year or '?'} - {item.end_year or 'present'}); field: {item.field_of_study or 'n/a'}; grade: {item.grade or 'n/a'}."
            for item in education
        ]
        documents.append({"title": "Education", "source": "/#education", "content": "\n".join(lines)})

    categories = SkillCategory.query.order_by(SkillCategory.display_order).all()
    if categories:
        lines = []
        for category in categories:
            skills = [skill.name for skill in category.skills if skill.is_visible]
            if skills:
                lines.append(f"{category.name}: {', '.join(skills)}")
        if lines:
            documents.append({"title": "Technical skills", "source": "/#skills", "content": "\n".join(lines)})

    for project in Project.query.filter_by(status="published", is_deleted=False).order_by(Project.display_order).all():
        metrics = "; ".join(
            f"{metric.name}: {metric.value}{(' ' + metric.unit) if metric.unit else ''}"
            for metric in project.metrics
        )
        content = "\n".join(
            filter(
                None,
                [
                    f"Project: {project.title}",
                    f"Type: {project.project_type or ''}",
                    f"Summary: {project.short_description}",
                    f"Problem: {project.problem_statement or ''}",
                    f"Solution: {project.solution or ''}",
                    f"Architecture: {project.architecture or ''}",
                    f"Implementation: {project.implementation or ''}",
                    f"Technologies: {', '.join(tech.name for tech in project.technologies)}",
                    f"Measured metrics: {metrics}" if metrics else "",
                    f"GitHub: {project.github_url or ''}",
                ],
            )
        )
        documents.append(
            {"title": f"Project - {project.title}", "source": f"/projects/{project.slug}", "content": content}
        )

    for research in ResearchProject.query.filter_by(status="published", is_deleted=False).all():
        metrics = "; ".join(
            f"{metric.name}: {metric.value}{(' ' + metric.unit) if metric.unit else ''}"
            for metric in research.metrics
        )
        content = "\n".join(
            filter(
                None,
                [
                    f"Research: {research.title}",
                    f"Abstract: {research.abstract or ''}",
                    f"Methodology: {research.methodology or ''}",
                    f"Sample size: {research.sample_size or ''}",
                    f"Institutions: {research.institutions_count or ''}",
                    f"Publication status: {research.publication_status or ''}",
                    f"Measured metrics: {metrics}" if metrics else "",
                ],
            )
        )
        documents.append(
            {"title": f"Research - {research.title}", "source": f"/research/{research.slug}", "content": content}
        )

    for certificate in Certificate.query.filter_by(status="published", is_deleted=False).all():
        documents.append(
            {
                "title": f"Certificate - {certificate.title}",
                "source": "/#certificates",
                "content": f"Issuer: {certificate.issuer}; issued: {certificate.issue_date or 'n/a'}; {certificate.description or ''}",
            }
        )

    for post in BlogPost.query.filter_by(status="published", is_deleted=False).all():
        documents.append(
            {
                "title": f"Blog - {post.title}",
                "source": f"/blog/{post.slug}",
                "content": f"{post.excerpt or ''}\n\n{(post.content or '')[:4000]}",
            }
        )

    for testimonial in Testimonial.query.filter_by(is_approved=True).all():
        documents.append(
            {
                "title": f"Testimonial - {testimonial.author_name}",
                "source": "/#testimonials",
                "content": f"{testimonial.author_name} ({testimonial.author_role or 'collaborator'}, {testimonial.organization or 'n/a'}): {testimonial.content}",
            }
        )
    return documents


def _knowledge_documents() -> list[dict]:
    chunks = (
        KnowledgeChunk.query.join(KnowledgeDocument)
        .filter(KnowledgeDocument.is_approved.is_(True), KnowledgeDocument.status == "indexed")
        .all()
    )
    return [
        {
            "title": chunk.document.title,
            "source": f"knowledge:{chunk.document.id}",
            "content": chunk.content,
            "embedding": chunk.embedding,
        }
        for chunk in chunks
    ]


def _lexical_scores(query: str, candidates: list[dict]) -> list[float]:
    query_tokens = Counter(_tokens(query))
    if not query_tokens:
        return [0.0] * len(candidates)
    doc_tokens = [Counter(_tokens(candidate["content"])) for candidate in candidates]
    document_frequency = Counter()
    for counts in doc_tokens:
        for token in query_tokens:
            if counts.get(token):
                document_frequency[token] += 1
    total = max(1, len(candidates))
    scores = []
    for counts in doc_tokens:
        score = 0.0
        for token, weight in query_tokens.items():
            frequency = counts.get(token, 0)
            if not frequency:
                continue
            idf = 1.0 + (total / (1 + document_frequency[token]))
            score += (1 + frequency ** 0.5) * idf * weight
        length_penalty = 1.0 + len(counts) / 1500
        scores.append(score / length_penalty)
    return scores


def retrieve(query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or current_app.config.get("AI_TOP_K", 5)
    candidates = _portfolio_documents() + _knowledge_documents()
    if not candidates:
        return []

    scores = _lexical_scores(query, candidates)
    vector = embed_texts([query])
    if vector:
        missing = [index for index, item in enumerate(candidates) if not item.get("embedding")]
        if missing:
            generated = embed_texts([candidates[index]["content"] for index in missing])
            if generated:
                for index, embedding in zip(missing, generated):
                    candidates[index]["embedding"] = embedding
        query_vector = vector[0]
        embedding_scores = [
            cosine_similarity(query_vector, item["embedding"]) if item.get("embedding") else 0.0
            for item in candidates
        ]
        scores = [0.55 * lex + 0.45 * emb for lex, emb in zip(scores, embedding_scores)]

    ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
    results = []
    for candidate, score in ranked[:top_k]:
        if score <= 0:
            continue
        results.append(
            {
                "title": candidate["title"],
                "source": candidate["source"],
                "content": candidate["content"][:1500],
                "score": round(float(score), 4),
            }
        )
    return results


def index_document(document: KnowledgeDocument) -> KnowledgeDocument:
    try:
        document.status = "processing"
        document.error_message = None
        db.session.commit()

        text = extract_text(document.file_path, document.mime_type)
        chunks = chunk_text(text)
        if not chunks:
            raise ValueError("No readable text found in document")

        KnowledgeChunk.query.filter_by(document_id=document.id).delete()
        vectors = embed_texts(chunks)
        for index, content in enumerate(chunks):
            db.session.add(
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                    embedding=vectors[index] if vectors else None,
                    token_estimate=max(1, len(content) // 4),
                )
            )
        document.chunk_count = len(chunks)
        document.status = "indexed"
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        document = db.session.get(KnowledgeDocument, document.id)
        if document is not None:
            document.status = "failed"
            document.error_message = str(exc)[:1000]
            document.chunk_count = 0
            db.session.commit()
    return document


def rebuild_index() -> dict:
    documents = KnowledgeDocument.query.all()
    indexed = 0
    chunks = 0
    for document in documents:
        if document.status == "failed" and not Path(document.file_path).exists():
            continue
        result = index_document(document)
        if result.status == "indexed":
            indexed += 1
            chunks += result.chunk_count
    return {
        "documents": indexed,
        "chunks": chunks,
        "backend": backend_name(),
        "portfolio_documents": len(_portfolio_documents()),
    }
