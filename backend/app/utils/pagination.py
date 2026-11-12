"""Query pagination, sorting and filtering utilities."""
from __future__ import annotations

from dataclasses import dataclass

from flask import request


@dataclass
class Pagination:
    page: int
    per_page: int
    total: int

    @property
    def pages(self) -> int:
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    def to_meta(self) -> dict:
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total": self.total,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
        }


def parse_pagination(default_per_page: int = 12, max_per_page: int = 100):
    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    page = max(page, 1)
    per_page = min(max(per_page, 1), max_per_page)
    return page, per_page


def paginate_query(query, page: int, per_page: int):
    total = query.order_by(None).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, Pagination(page=page, per_page=per_page, total=total)


def apply_sort(query, model, default: str = "-created_at"):
    """Apply ?sort=-field or a comma-separated list, restricted to model columns."""
    raw = request.args.get("sort", default).strip() or default
    clauses = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        descending = token.startswith("-")
        field_name = token.lstrip("-")
        column = getattr(model, field_name, None)
        if column is None or not hasattr(column, "asc"):
            continue
        clauses.append(column.desc() if descending else column.asc())
    if not clauses:
        fallback = getattr(model, "created_at", None)
        if fallback is not None:
            clauses.append(fallback.desc())
    return query.order_by(*clauses) if clauses else query


def get_bool_arg(name: str) -> bool | None:
    raw = request.args.get(name)
    if raw is None or raw == "":
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}
