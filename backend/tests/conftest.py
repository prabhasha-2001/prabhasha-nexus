import os
import shutil

import pytest

from app import create_app
from app.extensions import db
from app.models import AdminUser
from app.services.seed import seed_database


@pytest.fixture()
def app():
    application = create_app("testing")
    with application.app_context():
        db.drop_all()
        db.create_all()
        seed_database()
        yield application
        db.session.remove()
        db.drop_all()
    for path in (
        application.config["UPLOAD_DIR"],
        application.config["KNOWLEDGE_DIR"],
        application.config["FAISS_INDEX_DIR"],
        application.config["BACKUP_DIR"],
    ):
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="admin@test.local", password="TestPassword123!"):
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["data"]


@pytest.fixture()
def tokens(client):
    return login(client)


@pytest.fixture()
def auth(tokens):
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def role_headers(app, client):
    def _make(role: str, email: str | None = None):
        email = email or f"{role}@test.local"
        with app.app_context():
            user = AdminUser(name=f"{role.title()} User", email=email, role=role, is_active=True)
            user.set_password("RolePassword123!")
            db.session.add(user)
            db.session.commit()
        data = login(client, email=email, password="RolePassword123!")
        return {"Authorization": f"Bearer {data['access_token']}"}

    return _make
