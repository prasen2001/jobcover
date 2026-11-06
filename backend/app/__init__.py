from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from .config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    from .routes.auth import auth_bp
    from .routes.profile import profile_bp
    from .routes.resumes import resumes_bp
    from .routes.applications import applications_bp
    from .routes.latex import latex_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api/profile")
    app.register_blueprint(resumes_bp, url_prefix="/api/resumes")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(latex_bp, url_prefix="/api/latex")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "service": "jobcover-api"}

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(error="File is larger than the configured upload limit."), 413

    with app.app_context():
        db.create_all()
        _upgrade_local_schema()

    return app


def _upgrade_local_schema():
    """Apply small additive upgrades while this local-first app has no migration CLI."""
    inspector = inspect(db.engine)
    if "profile" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("profile")}
    if "program_name" not in columns:
        db.session.execute(text("ALTER TABLE profile ADD COLUMN program_name VARCHAR(255) DEFAULT ''"))
        db.session.commit()

