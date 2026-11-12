"""Provider-agnostic LLM client (Groq / OpenRouter, OpenAI-compatible APIs)."""
from __future__ import annotations

import requests
from flask import current_app

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMResult:
    def __init__(self, text: str | None, provider: str, model: str | None, error: str | None = None):
        self.text = text
        self.provider = provider
        self.model = model
        self.error = error

    @property
    def ok(self) -> bool:
        return bool(self.text)


def resolve_provider() -> tuple[str, str, str] | None:
    configured = (current_app.config.get("LLM_PROVIDER") or "auto").lower()
    if configured in {"auto", "groq"} and current_app.config.get("GROQ_API_KEY"):
        return "groq", GROQ_URL, current_app.config["GROQ_MODEL"]
    if configured in {"auto", "openrouter"} and current_app.config.get("OPENROUTER_API_KEY"):
        base = current_app.config["OPENROUTER_BASE_URL"].rstrip("/")
        return "openrouter", f"{base}/chat/completions", current_app.config["OPENROUTER_MODEL"]
    return None


def is_configured() -> bool:
    return resolve_provider() is not None


def complete(
    messages: list[dict],
    *,
    system: str | None = None,
    temperature: float = 0.3,
    max_tokens: int | None = None,
) -> LLMResult:
    provider = resolve_provider()
    if provider is None:
        return LLMResult(None, "unavailable", None, "No LLM API key configured")

    name, url, model = provider
    payload_messages = ([{"role": "system", "content": system}] if system else []) + messages
    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {current_app.config['GROQ_API_KEY' if name == 'groq' else 'OPENROUTER_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": payload_messages,
                "temperature": temperature,
                "max_tokens": max_tokens or current_app.config.get("AI_MAX_TOKENS", 700),
            },
            timeout=current_app.config.get("AI_TIMEOUT_SECONDS", 30),
        )
        response.raise_for_status()
        data = response.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        return LLMResult(text or None, name, model)
    except Exception as exc:
        current_app.logger.warning("LLM request failed: %s", exc)
        return LLMResult(None, name, model, str(exc))
