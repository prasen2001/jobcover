from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from .. import db
from ..models import Application, Resume, ResumeVersion, User
from ..services.ai import generate_cover_letter
from ..services.analysis import analyze_resume
from ..services.job_fetcher import fetch_job_description

applications_bp = Blueprint("applications", __name__)


@applications_bp.get("")
@jwt_required()
def list_applications():
    rows = Application.query.filter_by(user_id=int(get_jwt_identity())).order_by(Application.created_at.desc()).all()
    return jsonify(applications=[row.as_dict() for row in rows])


@applications_bp.post("/analyze")
@jwt_required()
def analyze():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    version = _owned_version(data.get("resumeVersionId"), user_id)
    if not version:
        return jsonify(error="Select a valid resume version."), 400
    try:
        job_text = _job_text(data)
    except Exception as exc:
        return jsonify(error=str(exc)), 422
    metrics = analyze_resume(version.parsed_text, job_text)
    application = Application(
        user_id=user_id,
        resume_version_id=version.id,
        company_name=str(data.get("companyName", "")).strip(),
        role_title=str(data.get("roleTitle", "")).strip(),
        job_url=str(data.get("jobUrl", "")).strip(),
        job_description=job_text,
        metrics_json=metrics,
    )
    db.session.add(application)
    db.session.commit()
    return jsonify(application=application.as_dict()), 201


@applications_bp.post("/<int:application_id>/cover-letter")
@jwt_required()
def cover_letter(application_id):
    user_id = int(get_jwt_identity())
    application = Application.query.filter_by(id=application_id, user_id=user_id).first_or_404()
    version = db.session.get(ResumeVersion, application.resume_version_id)
    user = db.session.get(User, user_id)
    try:
        application.cover_letter = generate_cover_letter(
            user.profile.as_dict(user.email), version.parsed_text, application.job_description,
            application.company_name, application.role_title, application.metrics_json,
        )
    except Exception as exc:
        return jsonify(error=f"Cover letter generation failed: {exc}"), 502
    db.session.commit()
    return jsonify(application=application.as_dict())


def _owned_version(version_id, user_id):
    if not version_id:
        return None
    return (
        ResumeVersion.query.join(Resume)
        .filter(ResumeVersion.id == version_id, Resume.user_id == user_id)
        .first()
    )


def _job_text(data):
    pasted = str(data.get("jobDescription", "")).strip()
    if len(pasted) >= 100:
        return pasted[:50_000]
    url = str(data.get("jobUrl", "")).strip()
    if url:
        return fetch_job_description(url)
    raise ValueError("Paste at least 100 characters of the job description or provide a job link.")
