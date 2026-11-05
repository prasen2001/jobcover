import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from .. import db
from ..models import Resume, ResumeVersion
from ..services.document_parser import parse_document

resumes_bp = Blueprint("resumes", __name__)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}


@resumes_bp.get("")
@jwt_required()
def list_resumes():
    user_id = int(get_jwt_identity())
    resumes = Resume.query.filter_by(user_id=user_id).order_by(Resume.created_at.desc()).all()
    return jsonify(resumes=[resume.as_dict() for resume in resumes])


@resumes_bp.post("")
@jwt_required()
def create_resume():
    user_id = int(get_jwt_identity())
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "General").strip() or "General"
    if not name:
        return jsonify(error="Resume name is required."), 400
    resume = Resume(user_id=user_id, name=name, category=category)
    db.session.add(resume)
    db.session.flush()
    result = _save_version(resume)
    if isinstance(result, tuple):
        db.session.rollback()
        return result
    db.session.commit()
    return jsonify(resume=resume.as_dict()), 201


@resumes_bp.post("/<int:resume_id>/versions")
@jwt_required()
def add_version(resume_id):
    resume = Resume.query.filter_by(id=resume_id, user_id=int(get_jwt_identity())).first_or_404()
    result = _save_version(resume)
    if isinstance(result, tuple):
        return result
    db.session.commit()
    return jsonify(resume=resume.as_dict()), 201


@resumes_bp.delete("/<int:resume_id>")
@jwt_required()
def delete_resume(resume_id):
    resume = Resume.query.filter_by(id=resume_id, user_id=int(get_jwt_identity())).first_or_404()
    paths = [Path(version.storage_path) for version in resume.versions]
    db.session.delete(resume)
    db.session.commit()
    for path in paths:
        path.unlink(missing_ok=True)
    return "", 204


def _save_version(resume):
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify(error="Choose a resume file to upload."), 400
    filename = secure_filename(upload.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify(error="Supported files: PDF, DOCX, TXT, and Markdown."), 400

    version_number = (
        db.session.query(func.max(ResumeVersion.version_number))
        .filter_by(resume_id=resume.id)
        .scalar()
        or 0
    ) + 1
    stored_name = f"{resume.user_id}_{resume.id}_v{version_number}_{uuid.uuid4().hex[:8]}.{extension}"
    storage_path = Path(current_app.config["UPLOAD_FOLDER"]) / stored_name
    upload.save(storage_path)
    parser_mode = request.form.get("parserMode", "").strip().lower() or None
    try:
        parsed_text, effective_mode = parse_document(storage_path, parser_mode)
    except Exception as exc:
        storage_path.unlink(missing_ok=True)
        return jsonify(error=f"Resume parsing failed: {exc}"), 422
    if not parsed_text.strip():
        storage_path.unlink(missing_ok=True)
        return jsonify(error="No readable text was found in the resume."), 422

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=version_number,
        original_filename=filename,
        storage_path=str(storage_path),
        parsed_text=parsed_text,
        parser_mode=effective_mode,
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(version)
    db.session.flush()
    return version

