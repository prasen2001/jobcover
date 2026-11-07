import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db


@pytest.fixture()
def app(tmp_path):
    class TestConfig:
        TESTING = True
        SECRET_KEY = "test-secret-that-is-long-enough-for-hmac"
        JWT_SECRET_KEY = "test-jwt-secret-that-is-at-least-32-bytes"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'test.db'}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        MAX_CONTENT_LENGTH = 2 * 1024 * 1024
        CORS_ORIGINS = ["http://localhost:5173"]
        JWT_ACCESS_TOKEN_EXPIRES = 3600
        LOG_FILE = str(tmp_path / "jobcover.log")
        LOG_LEVEL = "INFO"

    application = create_app(TestConfig)
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def token(client):
    response = client.post("/api/auth/signup", json={
        "fullName": "Alex Morgan",
        "email": "alex@example.com",
        "password": "correct-horse",
    })
    return response.get_json()["accessToken"]


@pytest.fixture()
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}

