"""Authenticated n8n webhook dispatch with execution logging."""
from __future__ import annotations

import time

import requests
from flask import current_app

from app.extensions import db
from app.models.automation import AutomationLog, AutomationWorkflow
from app.models.base import utcnow


def dispatch_event(event_key: str, payload: dict) -> list[dict]:
    """Send an event to every enabled workflow subscribed to event_key.

    Webhooks are optional: when n8n is not configured the event is recorded with
    status ``not_configured`` and never blocks the caller for long.
    """
    workflows = AutomationWorkflow.query.filter_by(event_key=event_key, is_enabled=True).all()
    results = []

    for workflow in workflows:
        started = time.perf_counter()
        log = AutomationLog(
            workflow_id=workflow.id,
            event_key=event_key,
            request_payload=payload,
        )
        webhook_url = workflow.webhook_url or _base_url_for(workflow)
        if not webhook_url:
            log.status = "not_configured"
            log.error_message = "No webhook URL configured"
            workflow.last_status = "not_configured"
            workflow.last_run_at = utcnow()
            db.session.add(log)
            db.session.commit()
            results.append(log.to_dict())
            continue

        headers = {"Content-Type": "application/json"}
        api_key = current_app.config.get("N8N_API_KEY")
        if api_key:
            headers["X-Nexus-Api-Key"] = api_key

        try:
            response = requests.post(
                webhook_url,
                json={"event": event_key, "payload": payload},
                headers=headers,
                timeout=current_app.config.get("N8N_TIMEOUT_SECONDS", 10),
            )
            log.response_code = response.status_code
            log.response_body = (response.text or "")[:2000]
            log.status = "success" if 200 <= response.status_code < 300 else "failed"
            workflow.last_status = log.status
        except Exception as exc:  # pragma: no cover - network dependent
            log.status = "failed"
            log.error_message = str(exc)
            workflow.last_status = "failed"

        log.duration_ms = int((time.perf_counter() - started) * 1000)
        workflow.last_run_at = utcnow()
        db.session.add(log)
        db.session.commit()
        results.append(log.to_dict())

    return results


def _base_url_for(workflow: AutomationWorkflow) -> str | None:
    base = current_app.config.get("N8N_WEBHOOK_BASE_URL")
    if not base:
        return None
    return f"{base.rstrip('/')}/{workflow.slug}"


def test_workflow(workflow: AutomationWorkflow) -> dict:
    """Dispatch a test payload to one workflow regardless of enabled state."""
    payload = {"test": True, "workflow": workflow.name, "triggered_from": "automation_center"}
    started = time.perf_counter()
    log = AutomationLog(
        workflow_id=workflow.id, event_key=workflow.event_key, request_payload=payload
    )
    webhook_url = workflow.webhook_url or _base_url_for(workflow)
    if not webhook_url:
        log.status = "not_configured"
        log.error_message = "No webhook URL configured"
    else:
        headers = {"Content-Type": "application/json"}
        api_key = current_app.config.get("N8N_API_KEY")
        if api_key:
            headers["X-Nexus-Api-Key"] = api_key
        try:
            response = requests.post(
                webhook_url,
                json={"event": workflow.event_key, "payload": payload},
                headers=headers,
                timeout=current_app.config.get("N8N_TIMEOUT_SECONDS", 10),
            )
            log.response_code = response.status_code
            log.response_body = (response.text or "")[:2000]
            log.status = "success" if 200 <= response.status_code < 300 else "failed"
        except Exception as exc:  # pragma: no cover - network dependent
            log.status = "failed"
            log.error_message = str(exc)

    log.duration_ms = int((time.perf_counter() - started) * 1000)
    workflow.last_status = log.status
    workflow.last_run_at = utcnow()
    db.session.add(log)
    db.session.commit()
    return log.to_dict()
