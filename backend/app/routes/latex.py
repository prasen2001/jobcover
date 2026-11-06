from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from .. import db
from ..models import Application, User
from ..services.latex_resume import (
    DEFAULT_GUARDRAILS,
    GUARDRAILS,
    LatexCompileError,
    LatexValidationError,
    compile_latex,
    default_model,
    generate_latex_resume,
    validate_grounded_facts,
    validate_guardrails,
    validate_meaningful_tailoring,
)

latex_bp = Blueprint("latex", __name__)


@latex_bp.get("/options")
@jwt_required()
def options():
    return jsonify(
        guardrails=[
            {"id": key, "label": _label(key), "description": description, "required": key == "preserve_facts"}
            for key, description in GUARDRAILS.items()
        ],
        defaultGuardrails=DEFAULT_GUARDRAILS,
    )


@latex_bp.post("/compile")
@jwt_required()
def compile_source():
    try:
        source = _uploaded_or_json_source()
        result = compile_latex(source, max_pages=5)
        return jsonify(result)
    except LatexValidationError as exc:
        return jsonify(error=str(exc)), 400
    except LatexCompileError as exc:
        return jsonify(error=str(exc)), 422


@latex_bp.post("/generate")
@jwt_required()
def generate():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    try:
        base_latex = str(data.get("latexCode", ""))
        guardrails = validate_guardrails(data.get("guardrails"))
        instructions = str(data.get("additionalInstructions", "")).strip()
        if len(instructions) > 2_000:
            raise LatexValidationError("Additional instructions must be 2,000 characters or fewer.")

        job_description = str(data.get("jobDescription", "")).strip()
        selected_suggestions = data.get("selectedSuggestions") or []
        if not isinstance(selected_suggestions, list) or len(selected_suggestions) > 20:
            raise LatexValidationError("Selected suggestions are invalid.")
        application_id = data.get("applicationId")
        if application_id:
            application = Application.query.filter_by(id=application_id, user_id=user_id).first()
            if not application:
                raise LatexValidationError("The selected job analysis was not found.")
            job_description = application.job_description
            available = application.metrics_json.get("suggestions", [])
            if any(item not in available for item in selected_suggestions):
                raise LatexValidationError("A selected suggestion does not belong to this job analysis.")
        elif selected_suggestions:
            raise LatexValidationError("Run or select a job analysis before applying its suggestions.")
        if len(job_description) < 100:
            raise LatexValidationError("Provide at least 100 characters of job description.")

        provider = str(data.get("provider") or "gemini").strip().lower()
        model_name = str(data.get("model") or default_model(provider)).strip()
        user = db.session.get(User, user_id)
        profile = user.profile.as_dict(user.email)
        generated = ""
        error = ""
        for attempt in range(2):
            try:
                generated = generate_latex_resume(
                    profile=profile,
                    base_latex=base_latex,
                    job_description=job_description,
                    suggestions=selected_suggestions,
                    guardrails=guardrails,
                    additional_instructions=instructions,
                    provider=provider,
                    model_name=model_name,
                    previous_output=generated if attempt else "",
                    compile_error=error,
                )
                validate_grounded_facts(base_latex, generated, profile)
                validate_meaningful_tailoring(base_latex, generated, guardrails)
                max_pages = 1 if "single_page" in guardrails else 2
                result = compile_latex(generated, max_pages=max_pages, guardrails=guardrails)
                return jsonify(result)
            except (LatexCompileError, LatexValidationError) as exc:
                error = str(exc)
        raise LatexCompileError(f"The generated resume could not satisfy the selected constraints after one repair attempt. {error}")
    except LatexValidationError as exc:
        return jsonify(error=str(exc)), 400
    except LatexCompileError as exc:
        return jsonify(error=str(exc)), 422
    except Exception as exc:
        return jsonify(error=f"Resume generation failed: {exc}"), 502


def _uploaded_or_json_source():
    upload = request.files.get("file")
    if upload and upload.filename:
        if not upload.filename.lower().endswith(".tex"):
            raise LatexValidationError("Only .tex source files can be uploaded here.")
        raw = upload.read(100_001)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise LatexValidationError("The .tex file must use UTF-8 text encoding.") from exc
    data = request.get_json(silent=True) or {}
    return str(data.get("latexCode", ""))


def _label(value):
    return value.replace("_", " ").title()
