"""Security, slug, hashing and secure upload helpers."""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.utils.errors import ApiError

MAGIC_SIGNATURES = {
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "gif": [b"GIF87a", b"GIF89a"],
    "webp": [b"RIFF"],
    "pdf": [b"%PDF-"],
}


def hash_value(value: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{value}".encode("utf-8")).hexdigest()


def hash_ip(ip: str, salt: str) -> str:
    return hash_value(ip or "unknown", salt)


def slugify(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value).strip("-")
    return value or secrets.token_hex(4)


def unique_slug(model, value: str, *, current_id: int | None = None) -> str:
    base = slugify(value)
    candidate = base
    counter = 2
    while True:
        query = model.query.filter_by(slug=candidate)
        if current_id is not None:
            query = query.filter(model.id != current_id)
        if query.first() is None:
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1


def _detect_kind(header: bytes, extension: str) -> bool:
    extension = extension.lower()
    signatures = MAGIC_SIGNATURES.get(extension)
    if not signatures:
        return False
    if extension == "webp":
        return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
    return any(header.startswith(sig) for sig in signatures)


def validate_upload(
    file: FileStorage,
    *,
    allowed_extensions: set[str],
    max_bytes: int,
) -> str:
    if file is None or not file.filename:
        raise ApiError("A file is required", status_code=400, code="validation_error")

    filename = secure_filename(file.filename)
    if "." not in filename:
        raise ApiError("File has no extension", status_code=415, code="unsupported_media_type")
    extension = filename.rsplit(".", 1)[1].lower()

    if extension not in allowed_extensions or extension not in MAGIC_SIGNATURES:
        raise ApiError(
            f"File type .{extension} is not allowed",
            status_code=415,
            code="unsupported_media_type",
            details={"allowed": sorted(allowed_extensions)},
        )

    header = file.stream.read(16)
    file.stream.seek(0)
    if not _detect_kind(header, extension):
        raise ApiError(
            "File content does not match its extension",
            status_code=415,
            code="unsupported_media_type",
        )

    if max_bytes and _stream_size(file) > max_bytes:
        raise ApiError(
            f"File exceeds the {max_bytes // (1024 * 1024)} MB limit",
            status_code=413,
            code="payload_too_large",
        )

    return extension


def _stream_size(file: FileStorage) -> int:
    stream = file.stream
    position = stream.tell()
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(position)
    return size


def save_upload(
    file: FileStorage,
    *,
    base_dir: str | Path,
    subdir: str = "media",
    allowed_extensions: set[str],
    max_bytes: int,
) -> dict:
    extension = validate_upload(
        file, allowed_extensions=allowed_extensions, max_bytes=max_bytes
    )
    original = secure_filename(file.filename)
    stem = Path(original).stem[:60] or "file"
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(6)
    filename = f"{timestamp}-{random_part}-{stem}.{extension}"

    target_dir = Path(base_dir) / subdir
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    file.save(target)

    checksum = _sha256_file(target)
    return {
        "filename": filename,
        "original_filename": original,
        "extension": extension,
        "path": str(target),
        "url": f"/uploads/{subdir}/{filename}",
        "size_bytes": target.stat().st_size,
        "checksum_sha256": checksum,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_safe_url(value: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", value or ""))
