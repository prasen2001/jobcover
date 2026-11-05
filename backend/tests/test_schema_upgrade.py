import sqlite3

from sqlalchemy import inspect, text

from app import create_app, db


def test_adds_program_to_existing_profile_table(tmp_path):
    database_path = tmp_path / "legacy.db"
    connection = sqlite3.connect(database_path)
    connection.execute(
        """CREATE TABLE profile (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            full_name VARCHAR(160) DEFAULT '',
            degree_name VARCHAR(255) DEFAULT ''
        )"""
    )
    connection.execute(
        "INSERT INTO profile (user_id, full_name, degree_name) VALUES (1, 'Alex', 'Bachelor of Science')"
    )
    connection.commit()
    connection.close()

    class LegacyConfig:
        TESTING = True
        SECRET_KEY = "test-secret-that-is-long-enough-for-hmac"
        JWT_SECRET_KEY = "test-jwt-secret-that-is-at-least-32-bytes"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{database_path}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        MAX_CONTENT_LENGTH = 2 * 1024 * 1024
        CORS_ORIGINS = ["http://localhost:5173"]
        JWT_ACCESS_TOKEN_EXPIRES = 3600

    application = create_app(LegacyConfig)
    with application.app_context():
        columns = {column["name"] for column in inspect(db.engine).get_columns("profile")}
        preserved = db.session.execute(text("SELECT full_name, degree_name FROM profile")).one()

    assert "program_name" in columns
    assert tuple(preserved) == ("Alex", "Bachelor of Science")
