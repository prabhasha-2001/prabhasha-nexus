"""GitHub integration and n8n automation routes."""
from __future__ import annotations

from flask import Blueprint, g, request

from app.automation.client import test_workflow
from app.extensions import db
from app.middleware.audit import log_activity
from app.middleware.auth import auth_required
from app.models import AutomationLog, AutomationWorkflow
from app.schemas import WorkflowSchema
from app.services import github_service
from app.utils.errors import NotFoundError
from app.utils.pagination import apply_sort, paginate_query, parse_pagination
from app.utils.responses import paginated_response, success_response
from app.utils.security import unique_slug

bp = Blueprint("integrations", __name__)


# ---------------------------------------------------------------- GitHub
@bp.get("/github/profile")
def github_profile():
    return success_response(github_service.get_profile())


@bp.get("/github/repos")
def github_repos():
    return success_response(github_service.get_repos())


@bp.get("/admin/github/overview")
@auth_required()
def github_overview():
    return success_response(
        {"profile": github_service.get_profile(), "repos": github_service.get_repos()}
    )


@bp.post("/admin/github/refresh")
@auth_required("admin")
def github_refresh():
    github_service.refresh()
    log_activity(g.current_user.id, "github.refresh", entity_type="github")
    return success_response({"message": "GitHub cache cleared"})


# ---------------------------------------------------------------- automation
@bp.get("/admin/automation/workflows")
@auth_required()
def list_workflows():
    items = AutomationWorkflow.query.order_by(AutomationWorkflow.name.asc()).all()
    return success_response([item.to_dict() for item in items])


@bp.post("/admin/automation/workflows")
@auth_required("admin")
def create_workflow():
    payload = WorkflowSchema().load(request.get_json(silent=True) or {})
    workflow = AutomationWorkflow(
        name=payload["name"],
        slug=unique_slug(AutomationWorkflow, payload["name"]),
        description=payload.get("description"),
        event_key=payload["event_key"],
        webhook_url=payload.get("webhook_url") or None,
        is_enabled=payload.get("is_enabled", False),
    )
    db.session.add(workflow)
    db.session.commit()
    log_activity(g.current_user.id, "automation.create", entity_type="automation_workflow",
                 entity_id=workflow.id)
    return success_response(workflow.to_dict(), status=201)


@bp.put("/admin/automation/workflows/<int:workflow_id>")
@auth_required("admin")
def update_workflow(workflow_id):
    workflow = db.session.get(AutomationWorkflow, workflow_id)
    if workflow is None:
        raise NotFoundError("Workflow not found")
    raw = request.get_json(silent=True) or {}
    payload = WorkflowSchema().load(raw, partial=True)
    for key, value in payload.items():
        if key in raw:
            setattr(workflow, key, value)
    if raw.get("webhook_url") == "":
        workflow.webhook_url = None
    db.session.commit()
    log_activity(g.current_user.id, "automation.update", entity_type="automation_workflow",
                 entity_id=workflow.id)
    return success_response(workflow.to_dict())


@bp.delete("/admin/automation/workflows/<int:workflow_id>")
@auth_required("admin")
def delete_workflow(workflow_id):
    workflow = db.session.get(AutomationWorkflow, workflow_id)
    if workflow is None:
        raise NotFoundError("Workflow not found")
    db.session.delete(workflow)
    db.session.commit()
    log_activity(g.current_user.id, "automation.delete", entity_type="automation_workflow",
                 entity_id=workflow_id)
    return success_response({"message": "Workflow deleted"})


@bp.post("/admin/automation/workflows/<int:workflow_id>/test")
@auth_required("admin")
def run_test(workflow_id):
    workflow = db.session.get(AutomationWorkflow, workflow_id)
    if workflow is None:
        raise NotFoundError("Workflow not found")
    result = test_workflow(workflow)
    log_activity(g.current_user.id, "automation.test", entity_type="automation_workflow",
                 entity_id=workflow.id, metadata={"status": result.get("status")})
    return success_response(result)


@bp.get("/admin/automation/logs")
@auth_required()
def list_logs():
    query = AutomationLog.query
    if request.args.get("status"):
        query = query.filter(AutomationLog.status == request.args["status"])
    if request.args.get("event_key"):
        query = query.filter(AutomationLog.event_key == request.args["event_key"])
    query = apply_sort(query, AutomationLog, default="-created_at")
    page, per_page = parse_pagination(default_per_page=25)
    items, pagination = paginate_query(query, page, per_page)
    return paginated_response([item.to_dict() for item in items], pagination)
