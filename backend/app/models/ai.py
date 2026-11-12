"""AI conversation, knowledge base and generation models."""
from __future__ import annotations

from app.extensions import db
from app.models.base import TimestampMixin, iso, utcnow

DOCUMENT_STATUSES = ("pending", "processing", "indexed", "failed")


class AIConversation(db.Model):
    __tablename__ = "ai_conversations"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=True)
    channel = db.Column(db.String(20), nullable=False, default="public")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    messages = db.relationship(
        "AIMessage", back_populates="conversation",
        cascade="all, delete-orphan", lazy="selectin", order_by="AIMessage.id",
    )

    def to_dict(self, detail: bool = False) -> dict:
        data = {
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "channel": self.channel,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
            "message_count": len(self.messages),
        }
        if detail:
            data["messages"] = [message.to_dict() for message in self.messages]
        return data


class AIMessage(db.Model):
    __tablename__ = "ai_messages"

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer, db.ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, default=list)
    agent = db.Column(db.String(60), nullable=True)
    tokens_used = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    conversation = db.relationship("AIConversation", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources or [],
            "agent": self.agent,
            "created_at": iso(self.created_at),
        }


class KnowledgeDocument(TimestampMixin, db.Model):
    __tablename__ = "knowledge_documents"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(600), nullable=False)
    mime_type = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False, default=0)
    checksum_sha256 = db.Column(db.String(64), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    is_approved = db.Column(db.Boolean, nullable=False, default=False, index=True)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    error_message = db.Column(db.Text, nullable=True)
    uploaded_by = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )

    chunks = db.relationship(
        "KnowledgeChunk", back_populates="document",
        cascade="all, delete-orphan", lazy="dynamic",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "status": self.status,
            "is_approved": self.is_approved,
            "chunk_count": self.chunk_count,
            "error_message": self.error_message,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }


class KnowledgeChunk(db.Model):
    __tablename__ = "knowledge_chunks"

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(
        db.Integer, db.ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chunk_index = db.Column(db.Integer, nullable=False, default=0)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.JSON, nullable=True)
    token_estimate = db.Column(db.Integer, nullable=True)

    document = db.relationship("KnowledgeDocument", back_populates="chunks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_estimate": self.token_estimate,
        }


class AIGeneration(TimestampMixin, db.Model):
    __tablename__ = "ai_generations"

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50), nullable=False, index=True)
    prompt = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="draft", index=True)
    provider = db.Column(db.String(50), nullable=True)
    model = db.Column(db.String(120), nullable=True)
    created_by = db.Column(
        db.Integer, db.ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "prompt": self.prompt,
            "output": self.output,
            "status": self.status,
            "provider": self.provider,
            "model": self.model,
            "created_at": iso(self.created_at),
            "updated_at": iso(self.updated_at),
        }
