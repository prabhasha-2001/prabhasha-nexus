from app.extensions import db
from app.models import AdminUser
from app.services.auth_service import create_password_reset


def test_login_success_and_me(client, tokens):
    assert tokens["user"]["email"] == "admin@test.local"
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["role"] == "admin"


def test_login_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/login", json={"email": "admin@test.local", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_refresh_and_logout(client, tokens):
    refresh_headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    rotated = client.post("/api/v1/auth/refresh", headers=refresh_headers)
    assert rotated.status_code == 200
    new_refresh = rotated.get_json()["data"]["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {new_refresh}"}
    )
    assert logout.status_code == 200

    reuse = client.post(
        "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {new_refresh}"}
    )
    assert reuse.status_code == 401


def test_change_password(client, auth):
    response = client.post(
        "/api/v1/auth/change-password",
        headers=auth,
        json={"current_password": "TestPassword123!", "new_password": "NewPassword123!"},
    )
    assert response.status_code == 200
    old = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "TestPassword123!"},
    )
    assert old.status_code == 401
    new = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "NewPassword123!"},
    )
    assert new.status_code == 200


def test_password_reset_flow(app, client):
    with app.app_context():
        token, _message = create_password_reset("admin@test.local")
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "ResetPassword123!"},
    )
    assert response.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "ResetPassword123!"},
    )
    assert login.status_code == 200

    reuse = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "AnotherPassword123!"},
    )
    assert reuse.status_code == 400


def test_account_lock_after_repeated_failures(client):
    for _ in range(5):
        client.post(
            "/api/v1/auth/login",
            json={"email": "admin@test.local", "password": "wrong-password"},
        )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.local", "password": "TestPassword123!"},
    )
    assert response.status_code == 423


def test_disabled_account_cannot_login(app, client):
    with app.app_context():
        user = AdminUser(name="Disabled", email="disabled@test.local", role="editor", is_active=False)
        user.set_password("DisabledPassword123!")
        db.session.add(user)
        db.session.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "disabled@test.local", "password": "DisabledPassword123!"},
    )
    assert response.status_code == 403
