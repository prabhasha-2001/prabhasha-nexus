"""Reusable admin CRUD engine for simple content resources."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from flask import request
from sqlalchemy import or_

from app.extensions import db
from app.middleware.audit import log_activity
from app.middleware.auth import current_user
from app.models.base import SoftDeleteMixin
from app.utils.errors import ApiError, NotFoundError
from app.utils.pagination import apply_sort, get_bool_arg, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response
from app.utils.security import unique_slug


@dataclass
class ResourceConfig:
    model: type
    schema: type | None = None
    resource: str = ""
    serializer: Callable | None = None
    search_fields: list[str] = field(default_factory=list)
    filter_map: dict[str, str] = field(default_factory=dict)
    default_sort: str = "-created_at"
    slug_source: str | None = None
    soft_delete: bool = False
    allow_create: bool = True
    allow_update: bool = True
    allow_delete: bool = True
    updatable_fields: list[str] = field(default_factory=list)
    entity_type: str | None = None
    after_create: Callable | None = None
    after_update: Callable | None = None

    def serialize(self, obj):
        if self.serializer:
            return self.serializer(obj)
        return obj.to_dict()


def _base_query(config: ResourceConfig):
    query = config.model.query
    if config.soft_delete:
        query = query.filter(config.model.is_deleted.is_(False))
    return query


def list_items(config: ResourceConfig):
    query = _base_query(config)
    search = request.args.get("q", "").strip()
    if search and config.search_fields:
        like = f"%{search}%"
        conditions = [getattr(config.model, field_name).ilike(like) for field_name in config.search_fields]
        query = query.filter(or_(*conditions))

    for param, column_name in config.filter_map.items():
        value = request.args.get(param)
        if value in (None, ""):
            continue
        column = getattr(config.model, column_name, None)
        if column is None:
            continue
        if isinstance(value, str) and value.lower() in {"true", "false"}:
            query = query.filter(column.is_(value.lower() == "true"))
        elif column.type.python_type is int and str(value).isdigit():
            query = query.filter(column == int(value))
        else:
            query = query.filter(column == value)

    query = apply_sort(query, config.model, default=config.default_sort)
    page, per_page = parse_pagination(default_per_page=20)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([config.serialize(item) for item in items], pagination)


def get_item(config: ResourceConfig, item_id: int):
    obj = _base_query(config).filter(config.model.id == item_id).first()
    if obj is None:
        raise NotFoundError(f"{config.resource or config.model.__name__} not found")
    return config.serialize(obj)


def _apply_columns(config: ResourceConfig, obj, data: dict):
    columns = {column.name for column in config.model.__table__.columns}
    for key, value in data.items():
        if key in columns and key not in {
            "id", "created_at", "updated_at", "is_deleted", "deleted_at", "views",
        }:
            setattr(obj, key, value)


def create_item(config: ResourceConfig):
    if not config.allow_create or config.schema is None:
        raise ApiError("Create is not supported for this resource", status_code=405,
                       code="method_not_allowed")
    payload = config.schema().load(request.get_json(silent=True) or {})
    obj = config.model()
    _apply_columns(config, obj, payload)
    if config.slug_source is not None:
        source_value = payload.get(config.slug_source) or ""
        setattr(obj, "slug", unique_slug(config.model, source_value))
    db.session.add(obj)
    db.session.commit()
    log_activity(
        _user_id(), f"{config.resource or config.model.__tablename__}.create",
        entity_type=config.entity_type or config.model.__tablename__, entity_id=obj.id,
    )
    if config.after_create:
        config.after_create(obj)
    return success_response(config.serialize(obj), status=201)


def update_item(config: ResourceConfig, item_id: int):
    if not config.allow_update:
        raise ApiError("Update is not supported for this resource", status_code=405,
                       code="method_not_allowed")
    obj = _base_query(config).filter(config.model.id == item_id).first()
    if obj is None:
        raise NotFoundError(f"{config.resource or config.model.__name__} not found")

    raw = request.get_json(silent=True) or {}
    payload = raw
    if config.schema is not None:
        loaded = config.schema().load(raw, partial=True)
        payload = {key: value for key, value in loaded.items() if key in raw}

    _apply_columns(config, obj, payload)
    if config.slug_source and payload.get(config.slug_source):
        setattr(obj, "slug", unique_slug(config.model, payload[config.slug_source], current_id=obj.id))

    db.session.commit()
    log_activity(
        _user_id(), f"{config.resource or config.model.__tablename__}.update",
        entity_type=config.entity_type or config.model.__tablename__, entity_id=obj.id,
    )
    if config.after_update:
        config.after_update(obj)
    return success_response(config.serialize(obj))


def delete_item(config: ResourceConfig, item_id: int):
    if not config.allow_delete:
        raise ApiError("Delete is not supported for this resource", status_code=405,
                       code="method_not_allowed")
    obj = db.session.get(config.model, item_id)
    if obj is None or (config.soft_delete and getattr(obj, "is_deleted", False)):
        raise NotFoundError(f"{config.resource or config.model.__name__} not found")

    if config.soft_delete and isinstance(obj, SoftDeleteMixin):
        obj.soft_delete()
    else:
        db.session.delete(obj)
    db.session.commit()
    log_activity(
        _user_id(), f"{config.resource or config.model.__tablename__}.delete",
        entity_type=config.entity_type or config.model.__tablename__, entity_id=item_id,
    )
    return success_response({"message": "Deleted"})


def _user_id() -> int | None:
    user = current_user()
    return user.id if user else None
