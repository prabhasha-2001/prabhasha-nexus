def test_viewer_can_read_but_not_write(client, role_headers):
    viewer = role_headers("viewer")
    assert client.get("/api/v1/admin/projects", headers=viewer).status_code == 200
    response = client.post(
        "/api/v1/admin/projects",
        headers=viewer,
        json={"title": "Forbidden Project", "short_description": "Viewers cannot create this."},
    )
    assert response.status_code == 403
    assert client.get("/api/v1/admin/users", headers=viewer).status_code == 403


def test_editor_can_manage_projects(client, role_headers):
    editor = role_headers("editor")
    response = client.post(
        "/api/v1/admin/projects",
        headers=editor,
        json={
            "title": "Nexus Test Project",
            "short_description": "A project created in the test suite.",
            "status": "published",
            "technologies": ["Python", "Flask"],
            "metrics": [
                {"name": "Accuracy", "value": "91.5", "unit": "%", "evaluation_run": "test-run"}
            ],
        },
    )
    assert response.status_code == 201
    project = response.get_json()["data"]
    assert project["slug"] == "nexus-test-project"
    assert project["technologies"] == ["Python", "Flask"]
    assert project["metrics"][0]["value"] == "91.5"

    detail = client.get(f"/api/v1/projects/{project['slug']}").get_json()["data"]
    assert detail["title"] == "Nexus Test Project"


def test_project_slug_is_unique(client, auth):
    payload = {
        "title": "Duplicate Title",
        "short_description": "First project with this title.",
        "status": "draft",
    }
    first = client.post("/api/v1/admin/projects", headers=auth, json=payload).get_json()["data"]
    second = client.post(
        "/api/v1/admin/projects",
        headers=auth,
        json={**payload, "short_description": "Second project with this title."},
    ).get_json()["data"]
    assert first["slug"] == "duplicate-title"
    assert second["slug"] == "duplicate-title-2"


def test_project_partial_update_preserves_fields(client, auth):
    created = client.post(
        "/api/v1/admin/projects",
        headers=auth,
        json={
            "title": "Partial Update",
            "short_description": "Original description for partial update.",
            "status": "draft",
            "display_order": 9,
        },
    ).get_json()["data"]
    updated = client.put(
        f"/api/v1/admin/projects/{created['id']}", headers=auth, json={"featured": True}
    ).get_json()["data"]
    assert updated["featured"] is True
    assert updated["short_description"] == "Original description for partial update."
    assert updated["status"] == "draft"
    assert updated["display_order"] == 9


def test_project_soft_delete_hides_from_public(client, auth):
    created = client.post(
        "/api/v1/admin/projects",
        headers=auth,
        json={
            "title": "Temporary Project",
            "short_description": "This project will be deleted.",
            "status": "published",
        },
    ).get_json()["data"]
    assert client.delete(f"/api/v1/admin/projects/{created['id']}", headers=auth).status_code == 200
    assert client.get(f"/api/v1/projects/{created['slug']}").status_code == 404
    listing = client.get("/api/v1/admin/projects?q=Temporary Project", headers=auth).get_json()["data"]
    assert listing == []


def test_generic_education_crud_keeps_partial_fields(client, auth):
    response = client.post(
        "/api/v1/admin/education",
        headers=auth,
        json={
            "institution": "Test University",
            "qualification": "BSc Test",
            "display_order": 5,
            "is_visible": True,
        },
    )
    assert response.status_code == 201
    item = response.get_json()["data"]
    updated = client.put(
        f"/api/v1/admin/education/{item['id']}",
        headers=auth,
        json={"grade": "First Class"},
    ).get_json()["data"]
    assert updated["grade"] == "First Class"
    assert updated["display_order"] == 5
    assert updated["is_visible"] is True
    assert client.delete(f"/api/v1/admin/education/{item['id']}", headers=auth).status_code == 200


def test_generic_skill_category_slug(client, auth):
    response = client.post(
        "/api/v1/admin/skill-categories",
        headers=auth,
        json={"name": "Test Category"},
    )
    assert response.status_code == 201
    assert response.get_json()["data"]["slug"] == "test-category"


def test_research_metrics_crud(client, auth):
    response = client.post(
        "/api/v1/admin/research",
        headers=auth,
        json={
            "title": "A Test Research Project",
            "status": "published",
            "metrics": [
                {"name": "F1", "value": "0.88", "metric_type": "model"},
                {"name": "Baseline", "value": "0.70", "metric_type": "baseline"},
            ],
        },
    )
    assert response.status_code == 201
    research = response.get_json()["data"]
    assert len(research["metrics"]) == 2
    client.put(
        f"/api/v1/admin/research/{research['id']}",
        headers=auth,
        json={"publication_status": "under_review"},
    )
    detail = client.get(f"/api/v1/admin/research/{research['id']}", headers=auth).get_json()["data"]
    assert detail["publication_status"] == "under_review"
    assert len(detail["metrics"]) == 2


def test_blog_crud_with_tags(client, auth):
    response = client.post(
        "/api/v1/admin/blogs",
        headers=auth,
        json={
            "title": "A Test Blog Post",
            "content": "This is a sufficiently long body for the blog post test.",
            "status": "published",
            "tags": ["Data Science", "Testing"],
        },
    )
    assert response.status_code == 201
    post = response.get_json()["data"]
    assert set(post["tags"]) == {"Data Science", "Testing"}
    public = client.get(f"/api/v1/blogs/{post['slug']}").get_json()["data"]
    assert public["title"] == "A Test Blog Post"


def test_user_management_rules(client, auth, tokens):
    response = client.post(
        "/api/v1/admin/users",
        headers=auth,
        json={
            "name": "New Editor",
            "email": "new-editor@test.local",
            "password": "EditorPassword123!",
            "role": "editor",
        },
    )
    assert response.status_code == 201
    user = response.get_json()["data"]
    assert user["role"] == "editor"

    self_delete = client.delete(f"/api/v1/admin/users/{tokens['user']['id']}", headers=auth)
    assert self_delete.status_code == 400

    assert client.delete(f"/api/v1/admin/users/{user['id']}", headers=auth).status_code == 200


def test_settings_update_and_activity_log(client, auth):
    response = client.put(
        "/api/v1/admin/settings",
        headers=auth,
        json={"settings": {"site_tagline": "Engineering with evidence"}},
    )
    assert response.status_code == 200
    values = {item["key"]: item["value"] for item in response.get_json()["data"]}
    assert values["site_tagline"] == "Engineering with evidence"

    logs = client.get("/api/v1/admin/activity-logs?action=settings", headers=auth).get_json()
    assert logs["meta"]["total"] >= 1


def test_docs_endpoints(client):
    assert client.get("/api/openapi.json").status_code == 200
    assert client.get("/api/docs").status_code == 200
