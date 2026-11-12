def test_track_page_view_and_summary(client, auth):
    response = client.post(
        "/api/v1/analytics/events",
        json={
            "event_type": "page_view",
            "path": "/projects/agriconnect",
            "page_type": "project",
            "visitor_id": "visitor-test-1",
            "device": "desktop",
            "referrer": "https://www.linkedin.com/feed/",
        },
    )
    assert response.status_code == 202
    assert response.get_json()["data"]["tracked"] is True

    summary = client.get("/api/v1/analytics/summary", headers=auth).get_json()["data"]
    assert summary["total_page_views"] >= 1
    assert summary["total_visitors"] >= 1
    assert summary["daily_series"]

    dashboard = client.get("/api/v1/admin/dashboard", headers=auth).get_json()["data"]
    assert dashboard["stats"]["total_page_views"] >= 1
    assert dashboard["traffic_sources"]


def test_invalid_event_type_rejected(client):
    response = client.post("/api/v1/analytics/events", json={"event_type": "hack"})
    assert response.status_code == 422


def test_project_view_tracking_via_public_detail(client, auth):
    slug = client.get("/api/v1/projects").get_json()["data"][0]["slug"]
    client.get(f"/api/v1/projects/{slug}")
    popular = client.get("/api/v1/analytics/popular", headers=auth).get_json()["data"]
    assert any(item["views"] >= 1 for item in popular.get("projects", []))


def test_analytics_csv_export(client, auth):
    client.post("/api/v1/analytics/events", json={"event_type": "page_view", "visitor_id": "csv-1"})
    response = client.get("/api/v1/analytics/export.csv?days=7", headers=auth)
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"date" in response.data.lower()
