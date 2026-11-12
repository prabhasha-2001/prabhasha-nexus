"""RAG-powered chatbot with deterministic fallback and conversation history."""
from __future__ import annotations

import secrets

from flask import current_app
from sqlalchemy import func

from app.ai import llm
from app.ai.rag_service import retrieve
from app.extensions import db
from app.models import AIConversation, AIMessage, Profile
from app.models.base import utcnow

SYSTEM_PROMPT = """You are the official portfolio assistant for Muwagamage Tharushi Prabhasha Dilshani.
Rules:
- Answer only from the verified CONTEXT provided. Never invent experience, certificates, employers,
  metrics, awards, or personal details.
- If the context does not contain the answer, say you do not have verified information and suggest
  using the contact form.
- Be concise, professional and helpful. Prefer short paragraphs or bullets.
- Mention source labels in plain text when useful, but do not fabricate URLs.
"""


def _contact_email() -> str:
    profile = Profile.query.order_by(Profile.id.asc()).first()
    return profile.email if profile and profile.email else "the contact form"


def _fallback_answer(message: str, sources: list[dict]) -> str:
    if not sources:
        return (
            "I do not have verified information about that yet. For anything not covered by the "
            f"portfolio, please reach out via {_contact_email()} or the contact form."
        )
    bullets = []
    for source in sources[:3]:
        snippet = " ".join(source["content"].split())
        if len(snippet) > 380:
            snippet = snippet[:377].rstrip() + "..."
        bullets.append(f"- {source['title']}: {snippet}")
    return (
        "Based on the verified portfolio content:\n"
        + "\n".join(bullets)
        + "\n\nAsk a more specific question if you want details about a project, skill, or research."
    )


def _conversation_for(session_id: str, channel: str, title: str | None = None) -> AIConversation:
    conversation = AIConversation.query.filter_by(session_id=session_id).first()
    if conversation is None:
        conversation = AIConversation(
            session_id=session_id, channel=channel, title=(title or "Portfolio chat")[:255]
        )
        db.session.add(conversation)
        db.session.flush()
    return conversation


def answer_chat(message: str, session_id: str | None = None, channel: str = "public") -> dict:
    session_id = (session_id or "").strip()[:64] or secrets.token_urlsafe(18)
    conversation = _conversation_for(session_id, channel, message[:120])

    history = [
        {"role": item.role, "content": item.content}
        for item in conversation.messages[-6:]
        if item.role in {"user", "assistant"}
    ]
    db.session.add(
        AIMessage(conversation_id=conversation.id, role="user", content=message[:4000])
    )
    db.session.commit()

    sources = retrieve(message)
    context = "\n\n".join(
        f"[{index + 1}] {source['title']} ({source['source']})\n{source['content']}"
        for index, source in enumerate(sources)
    )[: current_app.config.get("AI_MAX_CONTEXT_CHARS", 6000)]

    result = llm.complete(
        history + [{"role": "user", "content": f"CONTEXT:\n{context or 'No matching verified content.'}\n\nQUESTION: {message}"}],
        system=SYSTEM_PROMPT,
        temperature=0.2,
    )

    if result.ok:
        answer = result.text
        agent = "rag_llm"
        provider = result.provider
    else:
        answer = _fallback_answer(message, sources)
        agent = "rag_fallback"
        provider = "fallback"

    source_refs = [
        {"title": source["title"], "source": source["source"], "score": source["score"]}
        for source in sources
    ]
    db.session.add(
        AIMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            sources=source_refs,
            agent=agent,
        )
    )
    conversation.updated_at = utcnow()
    if not conversation.title:
        conversation.title = message[:120]
    db.session.commit()

    return {
        "session_id": session_id,
        "answer": answer,
        "sources": source_refs,
        "provider": provider,
        "agent": agent,
        "llm_configured": llm.is_configured(),
    }


def list_conversations(page: int, per_page: int):
    query = AIConversation.query.order_by(AIConversation.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return [conversation.to_dict() for conversation in pagination.items], pagination


def conversation_detail(conversation_id: int) -> dict:
    conversation = db.session.get(AIConversation, conversation_id)
    if conversation is None:
        return {}
    return conversation.to_dict(detail=True)


def unread_ai_metric() -> int:
    return int(db.session.query(func.count(AIConversation.id)).scalar() or 0)
