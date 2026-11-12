"""System health, settings, audit logs and backups."""
from __future__ import annotations

from flask import Blueprint, current_app, g, send_file, request
from sqlalchemy import text

from app.extensions import db
from app.middleware.audit import log_activity
from app.middleware.auth import auth_required
from app.models import AdminActivityLog, Notification, SystemSetting
from app.schemas import SettingsSchema
from app.services import backup_service
from app.utils.pagination import apply_sort, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response

bp = Blueprint("system", __name__)


@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"
    config = current_app.config
    return success_response(
        {
            "status": "ok" if database == "ok" else "degraded",
            "version": "1.0.0",
            "database": database,
            "integrations": {
                "llm_configured": bool(config.get("GROQ_API_KEY") or config.get("OPENROUTER_API_KEY")),
                "github_token_configured": bool(config.get("GITHUB_TOKEN")),
                "n8n_enabled": bool(config.get("N8N_ENABLED") and config.get("N8N_WEBHOOK_BASE_URL")),
                "smtp_configured": bool(config.get("MAIL_ENABLED") and config.get("SMTP_HOST")),
                "media_storage": config.get("MEDIA_STORAGE_BACKEND", "local"),
            },
        }
    )


@bp.get("/admin/settings")
@auth_required("admin")
def get_settings():
    settings = SystemSetting.query.order_by(SystemSetting.category.asc(), SystemSetting.key.asc()).all()
    return success_response([setting.to_dict() for setting in settings])


@bp.put("/admin/settings")
@auth_required("admin")
def update_settings():
    raw = request.get_json(silent=True) or {}
    values = raw.get("settings") if isinstance(raw.get("settings"), dict) else raw
    values = SettingsSchema().load({"settings": values})["settings"]
    updated = []
    for key, value in values.items():
        setting = SystemSetting.query.filter_by(key=key).first()
        if setting is None:
            setting = SystemSetting(key=key, value_json=value, category=raw.get("category", "general"))
            db.session.add(setting)
        else:
            setting.value_json = value
        updated.append(setting)
    db.session.commit()
    log_activity(g.current_user.id, "settings.update", entity_type="system_setting",
                 metadata={"keys": list(values.keys())})
    return success_response([setting.to_dict() for setting in updated])


@bp.get("/admin/activity-logs")
@auth_required()
def activity_logs():
    query = AdminActivityLog.query
    if request.args.get("action"):
        query = query.filter(AdminActivityLog.action.ilike(f"%{request.args['action']}%"))
    if request.args.get("entity_type"):
        query = query.filter(AdminActivityLog.entity_type == request.args["entity_type"])
    query = apply_sort(query, AdminActivityLog, default="-created_at")
    page, per_page = parse_pagination(default_per_page=30)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)


@bp.get("/admin/notifications/unread-count")
@auth_required()
def unread_notifications():
    return success_response({"count": Notification.query.filter_by(is_read=False).count()})


@bp.get("/admin/backups")
@auth_required("admin")
def list_backups():
    return success_response(backup_service.list_backups())


@bp.post("/admin/backups")
@auth_required("admin")
def create_backup():
    record = backup_service.create_backup()
    log_activity(g.current_user.id, "backup.create", entity_type="backup",
                 metadata={"filename": record["filename"]})
    return success_response(record, status=201)


@bp.get("/admin/backups/<filename>")
@auth_required("admin")
def download_backup(filename):
    path = backup_service.backup_path(filename)
    log_activity(g.current_user.id, "backup.download", entity_type="backup",
                 metadata={"filename": filename})
    return send_file(path, as_attachment=True, download_name=filename)
