"""Optional embedding backends with a deterministic lexical fallback."""
from __future__ import annotations

import math
import threading

from flask import current_app

_MODEL = None
_MODEL_LOCK = threading.Lock()
_MODEL_FAILED = False


def embeddings_enabled() -> bool:
    return bool(current_app.config.get("EMBEDDINGS_ENABLED", True))


def _load_model():
    global _MODEL, _MODEL_FAILED
    if _MODEL is not None or _MODEL_FAILED:
        return _MODEL
    if not embeddings_enabled():
        return None
    with _MODEL_LOCK:
        if _MODEL is not None or _MODEL_FAILED:
            return _MODEL
        try:
            from sentence_transformers import SentenceTransformer

            _MODEL = SentenceTransformer(current_app.config["EMBEDDING_MODEL"])
        except Exception:
            _MODEL_FAILED = True
            _MODEL = None
    return _MODEL


def backend_name() -> str:
    return "sentence-transformers" if _load_model() is not None else "lexical"


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    model = _load_model()
    if model is None or not texts:
        return None
    try:
        vectors = model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]
    except Exception:
        return None


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    norm_left = math.sqrt(sum(a * a for a in left))
    norm_right = math.sqrt(sum(b * b for b in right))
    if norm_left == 0 or norm_right == 0:
        return 0.0
    return dot / (norm_left * norm_right)
