"""Application configuration profiles."""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent


def _load_env():
    """Load .env from backend/ then repository root (first wins)."""
    for candidate in (BASE_DIR / ".env", ROOT_DIR / ".env"):
        if candidate.exists():
            load_dotenv(candidate, override=False)


_load_env()


def env_bool(name: str, default: bool = False) -> bool:
    return str(os.getenv(name, "true" if default else "false")).strip().lower() in {
        "1", "true", "yes", "on"
    }


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def env_path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else (BASE_DIR / path)


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _default_database_uri() -> str:
    configured = os.getenv("DATABASE_URL")
    if configured:
        return configured
    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(instance_dir / 'nexus.sqlite').as_posix()}"


class Config:
    # ---- Core ----
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-use-a-32-byte-env-value")
    JSON_SORT_KEYS = False
    PROPAGATE_EXCEPTIONS = None

    # ---- Database ----
    SQLALCHEMY_DATABASE_URI = _default_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---- JWT ----
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=env_int("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 120)
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=env_int("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7)
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_TYPE = "Bearer"

    # ---- CORS / URLs ----
    CORS_ORIGINS = env_list(
        "CORS_ORIGINS",
        "http://localhost:5500,http://127.0.0.1:5500,"
        "http://localhost:8080,http://127.0.0.1:8080,"
        "http://localhost:8000,http://127.0.0.1:8000,"
        "http://localhost:3000,http://127.0.0.1:3000,"
        "http://localhost:5173,http://127.0.0.1:5173,null",
    )
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")

    # ---- Rate limiting ----
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per hour")
    RATE_LIMIT_LOGIN = os.getenv("RATE_LIMIT_LOGIN", "10 per minute")
    RATE_LIMIT_CONTACT = os.getenv("RATE_LIMIT_CONTACT", "5 per hour")
    RATE_LIMIT_AI = os.getenv("RATE_LIMIT_AI", "20 per hour")
    RATELIMIT_HEADERS_ENABLED = True

    # ---- Uploads ----
    UPLOAD_DIR = env_path("UPLOAD_DIR", BASE_DIR / "uploads")
    MAX_CONTENT_LENGTH = env_int("MAX_CONTENT_LENGTH_MB", 25) * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf"}
    MEDIA_STORAGE_BACKEND = os.getenv("MEDIA_STORAGE_BACKEND", "local")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_REGION = os.getenv("S3_REGION", "")

    # ---- Admin seed ----
    ADMIN_NAME = os.getenv("ADMIN_NAME", "Prabhasha Dilshani")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@prabhashanexus.local")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeThisPassword123!")

    # ---- AI ----
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = env_int("EMBEDDING_DIMENSION", 384)
    AI_TOP_K = env_int("AI_TOP_K", 5)
    AI_MAX_CONTEXT_CHARS = env_int("AI_MAX_CONTEXT_CHARS", 6000)
    AI_MAX_TOKENS = env_int("AI_MAX_TOKENS", 700)
    AI_TIMEOUT_SECONDS = env_int("AI_TIMEOUT_SECONDS", 30)
    EMBEDDINGS_ENABLED = env_bool("EMBEDDINGS_ENABLED", True)
    KNOWLEDGE_DIR = env_path("KNOWLEDGE_DIR", BASE_DIR / "app" / "ai" / "documents")
    FAISS_INDEX_DIR = env_path("FAISS_INDEX_DIR", BASE_DIR / "app" / "ai" / "index")

    # ---- GitHub ----
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "prabhasha-2001")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_CACHE_TTL_SECONDS = env_int("GITHUB_CACHE_TTL_SECONDS", 600)

    # ---- n8n ----
    N8N_ENABLED = env_bool("N8N_ENABLED", False)
    N8N_WEBHOOK_BASE_URL = os.getenv("N8N_WEBHOOK_BASE_URL", "")
    N8N_API_KEY = os.getenv("N8N_API_KEY", "")
    N8N_TIMEOUT_SECONDS = env_int("N8N_TIMEOUT_SECONDS", 10)

    # ---- Mail ----
    MAIL_ENABLED = env_bool("MAIL_ENABLED", False)
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = env_int("SMTP_PORT", 587)
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@prabhashanexus.local")

    # ---- Analytics ----
    ANALYTICS_ENABLED = env_bool("ANALYTICS_ENABLED", True)
    ANALYTICS_SALT = os.getenv("ANALYTICS_SALT", "dev-analytics-salt")

    # ---- Backups ----
    BACKUP_DIR = env_path("BACKUP_DIR", BASE_DIR / "backups")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": __import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
    }
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False
    JWT_SECRET_KEY = "test-jwt-secret-key-with-at-least-32-bytes"
    SECRET_KEY = "test-secret-key-with-at-least-32-bytes"
    ADMIN_EMAIL = "admin@test.local"
    ADMIN_PASSWORD = "TestPassword123!"
    ANALYTICS_SALT = "test-salt"
    MEDIA_STORAGE_BACKEND = "local"
    UPLOAD_DIR = BASE_DIR / "tests" / "_uploads"
    KNOWLEDGE_DIR = BASE_DIR / "tests" / "_knowledge"
    FAISS_INDEX_DIR = BASE_DIR / "tests" / "_index"
    BACKUP_DIR = BASE_DIR / "tests" / "_backups"


class ProductionConfig(Config):
    DEBUG = False


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.getenv("FLASK_ENV") or "development").lower()
    return _CONFIGS.get(key, DevelopmentConfig)
