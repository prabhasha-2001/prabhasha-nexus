def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.get_json()
    assert body["success"] is True
    assert body["data"]["database"] == "ok"
    assert "integrations" in body["data"]


def test_public_portfolio_endpoints(client):
    for path in (
        "/api/v1/profile",
        "/api/v1/education",
        "/api/v1/skills",
        "/api/v1/projects",
        "/api/v1/projects/categories",
        "/api/v1/certificates",
        "/api/v1/research",
        "/api/v1/blogs",
        "/api/v1/testimonials",
        "/api/v1/resumes",
        "/api/v1/settings/public",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.get_json()["success"] is True


def test_project_detail_and_views(client):
    listing = client.get("/api/v1/projects").get_json()["data"]
    slug = listing[0]["slug"]
    response = client.get(f"/api/v1/projects/{slug}")
    assert response.status_code == 200
    project = response.get_json()["data"]
    assert "technologies" in project
    assert project["views"] >= 1


def test_research_detail_includes_metrics(client):
    listing = client.get("/api/v1/research").get_json()["data"]
    slug = listing[0]["slug"]
    response = client.get(f"/api/v1/research/{slug}")
    assert response.status_code == 200
    detail = response.get_json()["data"]
    types = {metric["metric_type"] for metric in detail["metrics"]}
    assert {"distribution", "model", "baseline"} <= types


def test_contact_validation(client):
    response = client.post("/api/v1/contact", json={"name": "x", "email": "bad"})
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "validation_error"


def test_contact_honeypot_does_not_persist(client, auth):
    response = client.post(
        "/api/v1/contact",
        json={
            "name": "Spam Bot",
            "email": "spam@example.com",
            "subject": "Spam",
            "message": "This should not be stored in the database.",
            "website": "http://spam.example",
        },
    )
    assert response.status_code == 200
    messages = client.get("/api/v1/admin/messages", headers=auth).get_json()["data"]
    assert messages == []


def test_contact_submission_and_admin_visibility(client, auth):
    response = client.post(
        "/api/v1/contact",
        json={
            "name": "Real Person",
            "email": "real@example.com",
            "subject": "Collaboration",
            "message": "I would like to discuss a project opportunity.",
        },
    )
    assert response.status_code == 201
    messages = client.get("/api/v1/admin/messages", headers=auth).get_json()["data"]
    assert len(messages) == 1
    assert messages[0]["status"] == "new"


def test_newsletter_requires_consent(client):
    response = client.post("/api/v1/newsletter", json={"email": "reader@example.com", "consent": False})
    assert response.status_code == 400
    response = client.post("/api/v1/newsletter", json={"email": "reader@example.com", "consent": True})
    assert response.status_code == 201
    duplicate = client.post("/api/v1/newsletter", json={"email": "reader@example.com", "consent": True})
    assert duplicate.status_code == 200


def test_unknown_project_returns_404(client):
    response = client.get("/api/v1/projects/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"
