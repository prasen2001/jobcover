import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")


def _project_path(value):
    path = Path(value).expanduser()
    return str(path if path.is_absolute() else PROJECT_ROOT / path)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'instance' / 'jobcover.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
    UPLOAD_FOLDER = str(BACKEND_DIR / "uploads")
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 24
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = _project_path(os.getenv("LOG_FILE", str(BACKEND_DIR / "logs" / "jobcover.log")))
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "3"))

