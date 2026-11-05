from email_validator import EmailNotValidError, validate_email
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from .. import db
from ..models import Profile, User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/signup")
def signup():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    full_name = str(data.get("fullName", "")).strip()
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError as exc:
        return jsonify(error=str(exc)), 400
    if len(password) < 8:
        return jsonify(error="Password must be at least 8 characters."), 400
    if User.query.filter_by(email=email).first():
        return jsonify(error="An account with this email already exists."), 409

    user = User(email=email)
    user.set_password(password)
    user.profile = Profile(full_name=full_name)
    db.session.add(user)
    db.session.commit()
    return jsonify(accessToken=create_access_token(identity=str(user.id)), user=_user_payload(user)), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(str(data.get("password", ""))):
        return jsonify(error="Invalid email or password."), 401
    return jsonify(accessToken=create_access_token(identity=str(user.id)), user=_user_payload(user))


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify(error="User not found."), 404
    return jsonify(user=_user_payload(user))


def _user_payload(user):
    return {"id": user.id, "email": user.email, "fullName": user.profile.full_name}

