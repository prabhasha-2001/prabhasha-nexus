"""Consistent JSON response helpers."""
from __future__ import annotations

from typing import Any

from flask import jsonify


def success_response(data: Any = None, *, meta: dict | None = None, status: int = 200):
    payload: dict[str, Any] = {"success": True, "data": data}
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status


def error_response(
    code: str,
    message: str,
    status: int = 400,
    details: Any = None,
):
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return jsonify({"success": False, "error": error}), status


def paginated_response(items: list, pagination, *, extra_meta: dict | None = None):
    meta = pagination.to_meta()
    if extra_meta:
        meta.update(extra_meta)
    return success_response(items, meta=meta)
