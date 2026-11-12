import json

from app.services import github_service


class FakeResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {"X-RateLimit-Remaining": "59", "X-RateLimit-Limit": "60"}
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def test_github_profile_uses_mocked_api(client, monkeypatch):
    github_service._CACHE.clear()

    def fake_get(url, headers=None, timeout=None):
        assert "api.github.com/users/prabhasha-2001" in url
        return FakeResponse(
            {
                "login": "prabhasha-2001",
                "name": "Prabhasha Dilshani",
                "bio": "Data science student",
                "avatar_url": "https://example.com/avatar.png",
                "html_url": "https://github.com/prabhasha-2001",
                "public_repos": 8,
                "followers": 5,
                "following": 3,
            }
        )

    monkeypatch.setattr(github_service.requests, "get", fake_get)
    response = client.get("/api/v1/github/profile")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["configured"] is True
    assert data["profile"]["login"] == "prabhasha-2001"
    github_service._CACHE.clear()


def test_github_overview_requires_auth_and_reports_errors(client, auth, monkeypatch):
    github_service._CACHE.clear()
    assert client.get("/api/v1/admin/github/overview").status_code == 401

    monkeypatch.setattr(
        github_service.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("network down")),
    )
    response = client.get("/api/v1/admin/github/overview", headers=auth)
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["profile"]["error"] == "network down"
    github_service._CACHE.clear()


def test_workflow_test_not_configured(client, auth):
    workflow = client.post(
        "/api/v1/admin/automation/workflows",
        headers=auth,
        json={"name": "Contact Sync", "event_key": "contact.created"},
    ).get_json()["data"]
    result = client.post(
        f"/api/v1/admin/automation/workflows/{workflow['id']}/test", headers=auth
    ).get_json()["data"]
    assert result["status"] == "not_configured"

    logs = client.get("/api/v1/admin/automation/logs", headers=auth).get_json()["data"]
    assert logs[0]["status"] == "not_configured"


def test_workflow_test_success_with_mocked_n8n(client, auth, monkeypatch):
    from app.automation import client as automation_client

    def fake_post(url, json=None, headers=None, timeout=None):
        assert url == "https://n8n.example/webhook/contact"
        assert json["event"] == "contact.created"
        return FakeResponse({"ok": True})

    monkeypatch.setattr(automation_client.requests, "post", fake_post)
    workflow = client.post(
        "/api/v1/admin/automation/workflows",
        headers=auth,
        json={
            "name": "Contact Webhook",
            "event_key": "contact.created",
            "webhook_url": "https://n8n.example/webhook/contact",
            "is_enabled": True,
        },
    ).get_json()["data"]

    result = client.post(
        f"/api/v1/admin/automation/workflows/{workflow['id']}/test", headers=auth
    ).get_json()["data"]
    assert result["status"] == "success"
    assert result["response_code"] == 200


def test_contact_submission_dispatches_enabled_workflow(client, auth, monkeypatch):
    from app.automation import client as automation_client

    calls = []

    def fake_post(url, json=None, headers=None, timeout=None):
        calls.append(json)
        return FakeResponse({"ok": True})

    monkeypatch.setattr(automation_client.requests, "post", fake_post)
    client.post(
        "/api/v1/admin/automation/workflows",
        headers=auth,
        json={
            "name": "Contact Event",
            "event_key": "contact.created",
            "webhook_url": "https://n8n.example/webhook/contact",
            "is_enabled": True,
        },
    )
    response = client.post(
        "/api/v1/contact",
        json={
            "name": "Workflow Tester",
            "email": "workflow@example.com",
            "subject": "Automation",
            "message": "Please trigger the configured webhook for this message.",
        },
    )
    assert response.status_code == 201
    assert len(calls) == 1
    assert calls[0]["event"] == "contact.created"
