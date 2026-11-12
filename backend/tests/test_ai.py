import io


def test_ai_status_reports_fallbacks(client):
    response = client.get("/api/v1/ai/status")
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["llm_configured"] is False
    assert data["retrieval_backend"] == "lexical"
    assert data["knowledge_documents"] == 0


def test_chat_fallback_uses_verified_portfolio(client, auth):
    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "Which projects has Prabhasha built?", "session_id": "session-abc"},
    )
    assert response.status_code == 200
    data = response.get_json()["data"]
    assert data["session_id"] == "session-abc"
    assert data["agent"] == "rag_fallback"
    assert data["provider"] == "fallback"
    assert data["sources"]
    assert any("Project" in source["title"] for source in data["sources"])
    assert "verified portfolio" in data["answer"].lower()

    conversation = client.get("/api/v1/admin/ai/conversations", headers=auth).get_json()["data"]
    assert len(conversation) == 1
    assert conversation[0]["message_count"] == 2

    detail = client.get(
        f"/api/v1/admin/ai/conversations/{conversation[0]['id']}", headers=auth
    ).get_json()["data"]
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]


def test_chat_validation(client):
    assert client.post("/api/v1/ai/chat", json={"message": ""}).status_code == 422


def test_knowledge_upload_requires_approval_before_retrieval(client, auth):
    response = client.post(
        "/api/v1/admin/ai/knowledge",
        headers=auth,
        data={
            "title": "Test Knowledge Note",
            "file": (
                io.BytesIO(
                    b"Prabhasha received the Golden Widget Award in 2026 for applied machine learning."
                ),
                "note.txt",
            ),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_json()
    document = response.get_json()["data"]
    assert document["status"] == "indexed"
    assert document["is_approved"] is False

    before = client.post(
        "/api/v1/ai/chat", json={"message": "What is the Golden Widget Award?"}
    ).get_json()["data"]
    assert not any("knowledge:" in source["source"] for source in before["sources"])

    approve = client.post(
        f"/api/v1/admin/ai/knowledge/{document['id']}/approve",
        headers=auth,
        json={"is_approved": True},
    )
    assert approve.status_code == 200
    assert approve.get_json()["data"]["is_approved"] is True

    after = client.post(
        "/api/v1/ai/chat", json={"message": "What is the Golden Widget Award?"}
    ).get_json()["data"]
    assert any("knowledge:" in source["source"] for source in after["sources"])
    assert "Golden Widget" in after["answer"]


def test_knowledge_upload_rejects_unsupported_type(client, auth):
    response = client.post(
        "/api/v1/admin/ai/knowledge",
        headers=auth,
        data={"file": (io.BytesIO(b"bad"), "note.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415


def test_knowledge_rebuild_and_delete(client, auth):
    upload = client.post(
        "/api/v1/admin/ai/knowledge",
        headers=auth,
        data={"file": (io.BytesIO(b"Verified note about data pipelines and SQL."), "note.md")},
        content_type="multipart/form-data",
    ).get_json()["data"]
    rebuilt = client.post("/api/v1/admin/ai/knowledge/rebuild", headers=auth).get_json()["data"]
    assert rebuilt["documents"] == 1
    assert rebuilt["chunks"] >= 1
    assert "backend" in rebuilt
    assert client.delete(f"/api/v1/admin/ai/knowledge/{upload['id']}", headers=auth).status_code == 200
    assert client.get("/api/v1/admin/ai/knowledge", headers=auth).get_json()["meta"]["total"] == 0


def test_content_generation_fallback_and_review(client, auth):
    response = client.post(
        "/api/v1/admin/ai/generate",
        headers=auth,
        json={
            "kind": "linkedin_post",
            "prompt": "Announce my data science portfolio launch",
            "context": "Focus on verified analytics projects.",
        },
    )
    assert response.status_code == 201
    record = response.get_json()["data"]
    assert record["provider"] == "template"
    assert record["status"] == "draft"
    assert "linkedin post" in record["output"].lower()

    review = client.put(
        f"/api/v1/admin/ai/generations/{record['id']}/review",
        headers=auth,
        json={"status": "approved"},
    )
    assert review.status_code == 200
    assert review.get_json()["data"]["status"] == "approved"

    listing = client.get("/api/v1/admin/ai/generations", headers=auth).get_json()["data"]
    assert listing[0]["id"] == record["id"]


def test_resume_analysis(client, auth):
    response = client.post(
        "/api/v1/admin/ai/resume/analyze",
        headers=auth,
        json={
            "job_description": (
                "We are hiring a data analyst with Python, SQL, Power BI, Excel, "
                "machine learning and REST API experience to build dashboards."
            ),
            "role_family": "Data Analyst",
        },
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["match_ratio"] > 0
    assert "python" in data["matched_keywords"]
    assert "Data Analyst" in data["output"]
