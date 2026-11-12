"""Analytics tracking and reporting routes."""
from __future__ import annotations

from flask import Blueprint, Response, current_app, request

from app.extensions import limiter
from app.middleware.auth import auth_required
from app.models import (
    AdminActivityLog,
    BlogPost,
    Certificate,
    ContactMessage,
    Project,
    ResumeDownload,
    Visitor,
)
from app.models.base import utcnow
from app.schemas import AnalyticsEventSchema
from app.services import analytics_service
from app.utils.responses import success_response

bp = Blueprint("analytics", __name__)


@bp.post("/analytics/events")
@limiter.limit("120 per hour")
def track_event():
    payload = AnalyticsEventSchema().load(request.get_json(silent=True) or {})
    stored = analytics_service.track_event(
        payload["event_type"],
        content_type=payload.get("content_type"),
        content_id=payload.get("content_id"),
        path=payload.get("path"),
        visitor_id=payload.get("visitor_id"),
        referrer=payload.get("referrer"),
        device=payload.get("device"),
        source=payload.get("source"),
        page_type=payload.get("page_type", "page"),
    )
    return success_response({"tracked": stored}, status=202 if stored else 200)


@bp.get("/admin/dashboard")
@auth_required()
def dashboard():
    period_days = 30
    data = analytics_service.summary(period_days)
    recent_activity = (
        AdminActivityLog.query.order_by(AdminActivityLog.created_at.desc()).limit(10).all()
    )
    return success_response(
        {
            "stats": {
                "total_visitors": data["total_visitors"],
                "total_page_views": data["total_page_views"],
                "total_projects": Project.query.filter(Project.is_deleted.is_(False)).count(),
                "published_projects": Project.query.filter(
                    Project.is_deleted.is_(False), Project.status == "published"
                ).count(),
                "total_certificates": Certificate.query.filter(
                    Certificate.is_deleted.is_(False)
                ).count(),
                "total_blog_posts": BlogPost.query.filter(
                    BlogPost.is_deleted.is_(False)
                ).count(),
                "published_blog_posts": BlogPost.query.filter(
                    BlogPost.is_deleted.is_(False), BlogPost.status == "published"
                ).count(),
                "total_contact_messages": ContactMessage.query.count(),
                "new_contact_messages": ContactMessage.query.filter_by(status="new").count(),
                "cv_downloads": ResumeDownload.query.count(),
                "unique_visitors_30d": Visitor.query.count(),
                "github_clicks_30d": data["github_clicks"],
            },
            "daily_series": data["daily_series"],
            "monthly_series": data["monthly_series"],
            "popular": analytics_service.popular(),
            "traffic_sources": analytics_service.traffic_sources(period_days),
            "recent_activity": [entry.to_dict() for entry in recent_activity],
        }
    )


@bp.get("/analytics/summary")
@auth_required()
def analytics_summary():
    days = _days_arg()
    return success_response(analytics_service.summary(days))


@bp.get("/analytics/popular")
@auth_required()
def analytics_popular():
    return success_response(analytics_service.popular())


@bp.get("/analytics/sources")
@auth_required()
def analytics_sources():
    return success_response(analytics_service.traffic_sources(_days_arg()))


@bp.get("/analytics/report")
@auth_required()
def analytics_report():
    days = _days_arg()
    return success_response(
        {
            "generated_at": utcnow().isoformat(),
            "summary": analytics_service.summary(days),
            "popular": analytics_service.popular(),
            "traffic_sources": analytics_service.traffic_sources(days),
            "note": "Predictions, when enabled, are labelled separately from measured data.",
        }
    )


@bp.get("/analytics/export.csv")
@auth_required()
def analytics_export():
    days = _days_arg()
    payload = analytics_service.export_csv(days)
    return Response(
        payload,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=nexus-analytics-{days}d.csv"
        },
    )


def _days_arg() -> int:
    try:
        days = int(request.args.get("days", 30))
    except (TypeError, ValueError):
        days = 30
    return min(max(days, 1), 365)
