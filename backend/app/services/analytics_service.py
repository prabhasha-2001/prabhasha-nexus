"""Privacy-conscious analytics tracking and aggregation."""
from __future__ import annotations

import csv
import io
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from urllib.parse import urlparse

from flask import current_app, request, has_request_context
from sqlalchemy import func

from app.extensions import db
from app.models import AnalyticsEvent, BlogPost, Certificate, ContactMessage, PageView, Project, Visitor
from app.models.base import utcnow
from app.utils.security import hash_ip


def _visitor_hash(visitor_id: str | None = None) -> str:
    salt = current_app.config.get("ANALYTICS_SALT", "")
    if visitor_id:
        return hash_ip(f"client:{visitor_id}", salt)
    if has_request_context():
        raw = f"{request.remote_addr}|{request.user_agent.string}"
    else:
        raw = "system"
    return hash_ip(raw, salt)


def _device_from(payload_device: str | None) -> str:
    if payload_device:
        return payload_device.lower()[:30]
    if not has_request_context():
        return "unknown"
    ua = (request.user_agent.string or "").lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    if "tablet" in ua or "ipad" in ua:
        return "tablet"
    return "desktop"


def track_event(
    event_type: str,
    *,
    content_type: str | None = None,
    content_id: int | None = None,
    path: str | None = None,
    visitor_id: str | None = None,
    referrer: str | None = None,
    device: str | None = None,
    source: str | None = None,
    page_type: str = "page",
    metadata: dict | None = None,
) -> bool:
    if not current_app.config.get("ANALYTICS_ENABLED", True):
        return False
    try:
        visitor_hash = _visitor_hash(visitor_id)
        referrer_host = _referrer_host(referrer)
        device_category = _device_from(device)
        source_value = (source or referrer_host or "direct")[:120]

        visitor = Visitor.query.filter_by(visitor_hash=visitor_hash).first()
        if visitor is None:
            visitor = Visitor(
                visitor_hash=visitor_hash,
                first_seen=utcnow(),
                last_seen=utcnow(),
                device_category=device_category,
                source=source_value,
            )
            db.session.add(visitor)
        else:
            visitor.last_seen = utcnow()

        if event_type == "page_view":
            db.session.add(
                PageView(
                    visitor_hash=visitor_hash,
                    path=(path or "/")[:500],
                    page_type=(page_type or "page")[:50],
                    content_id=content_id,
                    referrer_host=referrer_host,
                    device_category=device_category,
                )
            )

        db.session.add(
            AnalyticsEvent(
                visitor_hash=visitor_hash,
                event_type=event_type,
                content_type=content_type,
                content_id=content_id,
                metadata_json=metadata or {},
            )
        )
        db.session.commit()
        return True
    except Exception:  # analytics must never break a request
        db.session.rollback()
        current_app.logger.exception("Analytics tracking failed")
        return False


def _referrer_host(referrer: str | None) -> str | None:
    if not referrer:
        return None
    try:
        host = urlparse(referrer).hostname
        return host[:200] if host else None
    except Exception:
        return None


def _since(days: int) -> datetime:
    return utcnow() - timedelta(days=max(1, days))


def summary(days: int = 30) -> dict:
    since = _since(days)
    page_view_rows = (
        db.session.query(PageView.visitor_hash, PageView.created_at, PageView.device_category)
        .filter(PageView.created_at >= since)
        .all()
    )
    event_rows = (
        db.session.query(AnalyticsEvent.event_type, AnalyticsEvent.content_type, AnalyticsEvent.content_id,
                         AnalyticsEvent.created_at)
        .filter(AnalyticsEvent.created_at >= since)
        .all()
    )

    daily_visitors: dict[str, set] = defaultdict(set)
    daily_views: Counter = Counter()
    devices: Counter = Counter()
    for visitor_hash, created_at, device_category in page_view_rows:
        day = created_at.strftime("%Y-%m-%d")
        daily_visitors[day].add(visitor_hash)
        daily_views[day] += 1
        if device_category:
            devices[device_category] += 1

    event_counts = Counter(row[0] for row in event_rows)
    all_days = sorted(daily_views.keys())
    series = [
        {
            "date": day,
            "visitors": len(daily_visitors.get(day, set())),
            "page_views": daily_views.get(day, 0),
        }
        for day in all_days
    ]

    visitors = {
        row[0] for row in db.session.query(PageView.visitor_hash).filter(PageView.created_at >= since).all()
    }
    cv_downloads = event_counts.get("cv_download", 0)
    github_clicks = event_counts.get("github_click", 0)
    contact_submissions = ContactMessage.query.filter(ContactMessage.created_at >= since).count()

    return {
        "period_days": days,
        "from": since.isoformat(),
        "to": utcnow().isoformat(),
        "total_visitors": len(visitors),
        "total_page_views": len(page_view_rows),
        "total_events": len(event_rows),
        "cv_downloads": cv_downloads,
        "github_clicks": github_clicks,
        "contact_submissions": contact_submissions,
        "event_counts": dict(event_counts),
        "devices": dict(devices),
        "daily_series": series,
        "monthly_series": _monthly_series(page_view_rows),
        "prediction": None,
    }


def _monthly_series(rows) -> list[dict]:
    visitors: dict[str, set] = defaultdict(set)
    views: Counter = Counter()
    for visitor_hash, created_at, _device in rows:
        month = created_at.strftime("%Y-%m")
        visitors[month].add(visitor_hash)
        views[month] += 1
    return [
        {"month": month, "visitors": len(visitors[month]), "page_views": views[month]}
        for month in sorted(views.keys())
    ]


def popular(limit: int = 5) -> dict:
    projects = (
        Project.query.filter(Project.is_deleted.is_(False))
        .order_by(Project.views.desc())
        .limit(limit)
        .all()
    )
    posts = (
        BlogPost.query.filter(BlogPost.is_deleted.is_(False))
        .order_by(BlogPost.views.desc())
        .limit(limit)
        .all()
    )
    certificates = Certificate.query.filter(Certificate.is_deleted.is_(False)).order_by(
        Certificate.views.desc()
    ).limit(limit).all()
    content_clicks = (
        db.session.query(AnalyticsEvent.content_type, AnalyticsEvent.content_id, func.count())
        .filter(AnalyticsEvent.event_type.in_(["project_view", "blog_view", "certificate_view"]))
        .group_by(AnalyticsEvent.content_type, AnalyticsEvent.content_id)
        .order_by(func.count().desc())
        .limit(limit)
        .all()
    )
    return {
        "projects": [
            {"id": p.id, "title": p.title, "slug": p.slug, "views": p.views} for p in projects
        ],
        "blog_posts": [
            {"id": p.id, "title": p.title, "slug": p.slug, "views": p.views} for p in posts
        ],
        "certificates": [
            {"id": c.id, "title": c.title, "views": c.views} for c in certificates
        ],
        "tracked_clicks": [
            {"content_type": row[0], "content_id": row[1], "count": row[2]}
            for row in content_clicks
        ],
    }


def traffic_sources(days: int = 30) -> list[dict]:
    since = _since(days)
    rows = (
        db.session.query(PageView.referrer_host, func.count())
        .filter(PageView.created_at >= since)
        .group_by(PageView.referrer_host)
        .order_by(func.count().desc())
        .all()
    )
    return [
        {"source": row[0] or "direct", "count": row[1]} for row in rows
    ]


def export_csv(days: int = 30) -> str:
    data = summary(days)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["date", "visitors", "page_views"])
    for row in data["daily_series"]:
        writer.writerow([row["date"], row["visitors"], row["page_views"]])
    writer.writerow([])
    writer.writerow(["metric", "value"])
    writer.writerow(["total_visitors", data["total_visitors"]])
    writer.writerow(["total_page_views", data["total_page_views"]])
    writer.writerow(["cv_downloads", data["cv_downloads"]])
    writer.writerow(["github_clicks", data["github_clicks"]])
    writer.writerow(["contact_submissions", data["contact_submissions"]])
    return buffer.getvalue()
