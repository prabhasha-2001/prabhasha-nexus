"""Centralized error types and handlers."""
from __future__ import annotations

import logging

from flask import Flask, current_app
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge, UnsupportedMediaType

from app.utils.responses import error_response

logger = logging.getLogger(__name__)


class ApiError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None, details=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code
        self.details = details


class NotFoundError(ApiError):
    status_code = 404
    code = "not_found"


class ConflictError(ApiError):
    status_code = 409
    code = "conflict"


class ForbiddenError(ApiError):
    status_code = 403
    code = "forbidden"


class UnauthorizedError(ApiError):
    status_code = 401
    code = "unauthorized"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        return error_response(exc.code, exc.message, exc.status_code, exc.details)

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        return error_response(
            "validation_error", "Request validation failed", 422, exc.messages
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(exc):
        limit_mb = current_app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return error_response(
            "payload_too_large", f"Upload exceeds the {limit_mb} MB limit", 413
        )

    @app.errorhandler(UnsupportedMediaType)
    def handle_unsupported(exc):
        return error_response(
            "unsupported_media_type", "Unsupported media type", 415
        )

    @app.errorhandler(IntegrityError)
    def handle_integrity(exc):
        from app.extensions import db

        db.session.rollback()
        logger.warning("Integrity error: %s", exc)
        return error_response(
            "conflict", "The request conflicts with existing data", 409
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        code_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            409: "conflict",
            413: "payload_too_large",
            415: "unsupported_media_type",
            429: "rate_limited",
        }
        code = code_map.get(exc.code or 500, "http_error")
        message = exc.description or exc.name
        return error_response(code, message, exc.code or 500)

    @app.errorhandler(429)
    def handle_rate_limit(exc):
        return error_response(
            "rate_limited", "Too many requests. Please try again later.", 429
        )

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        from app.extensions import db

        db.session.rollback()
        logger.exception("Unhandled exception")
        if current_app.debug:
            raise exc
        return error_response(
            "internal_error", "An unexpected error occurred", 500
        )
