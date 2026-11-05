from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from .. import db
from ..models import Profile, User

profile_bp = Blueprint("profile", __name__)

FIELD_MAP = {
    "fullName": "full_name",
    "phone": "phone",
    "location": "location",
    "linkedinUrl": "linkedin_url",
    "portfolioUrl": "portfolio_url",
    "collegeName": "college_name",
    "degreeName": "degree_name",
    "programName": "program_name",
    "enrollmentYear": "enrollment_year",
    "graduationYear": "graduation_year",
    "professionalSummary": "professional_summary",
    "skills": "skills",
}


@profile_bp.get("")
@jwt_required()
def get_profile():
    user = _current_user()
    return jsonify(profile=user.profile.as_dict(user.email))


@profile_bp.put("")
@jwt_required()
def update_profile():
    user = _current_user()
    data = request.get_json(silent=True) or {}
    if not user.profile:
        user.profile = Profile()
    for client_name, model_name in FIELD_MAP.items():
        if client_name in data:
            value = data[client_name]
            if client_name in {"enrollmentYear", "graduationYear"}:
                value = int(value) if value not in (None, "") else None
            setattr(user.profile, model_name, value)
    db.session.commit()
    return jsonify(profile=user.profile.as_dict(user.email))


def _current_user():
    return db.session.get(User, int(get_jwt_identity()))

