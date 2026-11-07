import pytest

from app.services import latex_resume
from app.services.latex_resume import (
    LatexValidationError,
    _extract_latex,
    validate_guardrails,
    validate_grounded_facts,
    validate_latex_source,
    validate_meaningful_tailoring,
    validate_tailoring_mode,
)


SAFE_SOURCE = r"""\documentclass[10pt]{article}
\usepackage[margin=0.6in]{geometry}
\begin{document}
Alex Morgan\\
Software engineer with Python experience.
\end{document}
"""


def test_accepts_safe_standalone_resume():
    assert validate_latex_source(SAFE_SOURCE) == SAFE_SOURCE.strip()


def test_allows_standard_glyph_to_unicode_input():
    source = SAFE_SOURCE.replace(
        r"\begin{document}",
        "\\usepackage{iftex}\n\\ifPDFTeX\n"
        "\\IfFileExists{glyphtounicode.tex}{\\input{glyphtounicode}}{}\n"
        "\\pdfgentounicode=1\n\\fi\n\\begin{document}",
    )
    assert validate_latex_source(source)


def test_still_rejects_every_other_input_target():
    source = SAFE_SOURCE.replace(r"\begin{document}", r"\input{resume-secrets}\begin{document}")
    with pytest.raises(LatexValidationError, match=r"\\input"):
        validate_latex_source(source)


@pytest.mark.parametrize("command", [r"\input{secret}", r"\write18{curl example.com}", r"\includegraphics{photo}"])
def test_rejects_latex_file_and_shell_commands(command):
    source = SAFE_SOURCE.replace(r"\begin{document}", rf"\begin{{document}}{command}")
    with pytest.raises(LatexValidationError, match="not allowed"):
        validate_latex_source(source)


@pytest.mark.parametrize("command", [r"\begin{filecontents}{x}", r"\scantokens{test}", r"^^69nput{secret}"])
def test_rejects_encoded_or_file_backed_features(command):
    source = SAFE_SOURCE.replace(r"\begin{document}", rf"\begin{{document}}{command}")
    with pytest.raises(LatexValidationError, match="not allowed"):
        validate_latex_source(source)


def test_rejects_non_allowlisted_package():
    source = SAFE_SOURCE.replace(r"\begin{document}", r"\usepackage{minted}\begin{document}")
    with pytest.raises(LatexValidationError, match="allowlist"):
        validate_latex_source(source)


def test_truthfulness_guardrail_cannot_be_disabled():
    assert validate_guardrails([]) == ["preserve_facts"]


def test_readable_spacing_is_preselected_by_default():
    assert "readable_spacing" in validate_guardrails(None)


def test_maximum_match_is_the_default_tailoring_mode():
    assert validate_tailoring_mode(None) == "maximum_match"
    with pytest.raises(LatexValidationError, match="Tailoring mode"):
        validate_tailoring_mode("guaranteed_hire")


def test_local_latex_model_uses_document_sized_context(monkeypatch):
    captured = {}

    def fake_ollama(model_name, **kwargs):
        captured.update(model_name=model_name, **kwargs)
        return object()

    monkeypatch.setattr(latex_resume, "_ollama_model", fake_ollama)
    monkeypatch.setenv("OLLAMA_LATEX_CONTEXT_LENGTH", "16384")
    monkeypatch.setenv("OLLAMA_LATEX_MAX_TOKENS", "4096")
    latex_resume._chat_model("ollama", "llama3.1:8b")
    assert captured == {"model_name": "llama3.1:8b", "num_ctx": 16384, "num_predict": 4096}


def test_rejects_new_numeric_claims_from_generated_resume():
    generated = SAFE_SOURCE.replace("Python experience", "Python experience that improved revenue by 42%")
    with pytest.raises(LatexValidationError, match="unsupported number"):
        validate_grounded_facts(SAFE_SOURCE, generated, {"fullName": "Alex Morgan"})


def test_accepts_numbers_already_supported_by_source():
    source = SAFE_SOURCE.replace("Python experience", "Python experience that improved latency by 35%")
    validate_grounded_facts(source, source, {"fullName": "Alex Morgan"})


def test_rejects_an_unchanged_resume_when_job_relevance_is_selected():
    with pytest.raises(LatexValidationError, match="identical to the source"):
        validate_meaningful_tailoring(SAFE_SOURCE, SAFE_SOURCE, ["job_relevance"])


def test_accepts_a_meaningfully_tailored_resume():
    tailored = SAFE_SOURCE.replace(
        "Software engineer with Python experience.",
        "Python engineer who builds reliable APIs and distributed services.",
    )
    validate_meaningful_tailoring(SAFE_SOURCE, tailored, ["job_relevance"])


def test_extracts_document_from_model_fence():
    result = _extract_latex(f"Here it is:\n```latex\n{SAFE_SOURCE}\n```")
    assert result.startswith(r"\documentclass")
    assert result.endswith(r"\end{document}")


def test_latex_options_are_authenticated(client):
    assert client.get("/api/latex/options").status_code == 401


def test_latex_options_include_required_truthfulness(client, auth_headers):
    response = client.get("/api/latex/options", headers=auth_headers)
    facts = next(item for item in response.get_json()["guardrails"] if item["id"] == "preserve_facts")
    assert response.status_code == 200
    assert facts["required"] is True
    assert response.get_json()["defaultTailoringMode"] == "maximum_match"
    assert {item["id"] for item in response.get_json()["tailoringModes"]} == {"balanced", "maximum_match"}


def test_compile_route_returns_pdf_payload(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.routes.latex.compile_latex",
        lambda source, **kwargs: {"latexCode": source.strip(), "pdfBase64": "JVBERi0=", "pageCount": 1},
    )
    response = client.post("/api/latex/compile", headers=auth_headers, json={"latexCode": SAFE_SOURCE})
    assert response.status_code == 200
    assert response.get_json()["pageCount"] == 1


def test_user_can_create_update_list_and_delete_latex_template(client, auth_headers):
    created = client.post("/api/latex/templates", headers=auth_headers, json={
        "name": "Backend resume",
        "latexCode": SAFE_SOURCE,
    })
    assert created.status_code == 201
    template_id = created.get_json()["template"]["id"]

    listed = client.get("/api/latex/templates", headers=auth_headers)
    assert listed.status_code == 200
    assert listed.get_json()["templates"][0]["latexCode"] == SAFE_SOURCE.strip()

    updated_source = SAFE_SOURCE.replace("Python experience", "Python and Flask experience")
    updated = client.put(f"/api/latex/templates/{template_id}", headers=auth_headers, json={
        "name": "Backend resume v2",
        "latexCode": updated_source,
    })
    assert updated.status_code == 200
    assert updated.get_json()["template"]["name"] == "Backend resume v2"

    deleted = client.delete(f"/api/latex/templates/{template_id}", headers=auth_headers)
    assert deleted.status_code == 204
    assert client.get("/api/latex/templates", headers=auth_headers).get_json()["templates"] == []


def test_latex_templates_are_private_and_validate_source(client, auth_headers):
    invalid = client.post("/api/latex/templates", headers=auth_headers, json={
        "name": "Unsafe",
        "latexCode": r"\documentclass{article}\begin{document}\input{secret}\end{document}",
    })
    assert invalid.status_code == 400

    created = client.post("/api/latex/templates", headers=auth_headers, json={
        "name": "Private template",
        "latexCode": SAFE_SOURCE,
    })
    template_id = created.get_json()["template"]["id"]
    second_signup = client.post("/api/auth/signup", json={
        "fullName": "Taylor Smith",
        "email": "taylor@example.com",
        "password": "correct-horse",
    })
    other_headers = {"Authorization": f"Bearer {second_signup.get_json()['accessToken']}"}
    assert client.get("/api/latex/templates", headers=other_headers).get_json()["templates"] == []
    assert client.delete(f"/api/latex/templates/{template_id}", headers=other_headers).status_code == 404


def test_generate_route_applies_guardrails_and_returns_render(client, auth_headers, monkeypatch):
    captured = {}

    def fake_generate(**kwargs):
        captured.update(kwargs)
        return SAFE_SOURCE

    monkeypatch.setattr("app.routes.latex.generate_latex_resume", fake_generate)
    monkeypatch.setattr(
        "app.routes.latex.compile_latex",
        lambda source, **kwargs: {"latexCode": source.strip(), "pdfBase64": "JVBERi0=", "pageCount": 1},
    )
    response = client.post("/api/latex/generate", headers=auth_headers, json={
        "latexCode": SAFE_SOURCE,
        "jobDescription": "We need a software engineer with Python, Flask, React, testing, API design, clear communication, reliable delivery, and cross-functional collaboration.",
        "guardrails": ["single_page", "ats_safe"],
        "additionalInstructions": "Keep education.",
        "provider": "ollama",
        "model": "llama3.1:8b",
    })
    assert response.status_code == 200
    assert response.get_json()["pageCount"] == 1
    assert "preserve_facts" in captured["guardrails"]
    assert captured["additional_instructions"] == "Keep education."
    assert captured["tailoring_mode"] == "maximum_match"


def test_generate_route_retries_an_incomplete_model_document(client, auth_headers, monkeypatch):
    calls = []

    def generate_once_incomplete(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise LatexValidationError("The model did not return a complete LaTeX document.")
        return SAFE_SOURCE

    monkeypatch.setattr("app.routes.latex.generate_latex_resume", generate_once_incomplete)
    monkeypatch.setattr(
        "app.routes.latex.compile_latex",
        lambda source, **kwargs: {"latexCode": source.strip(), "pdfBase64": "JVBERi0=", "pageCount": 1},
    )
    response = client.post("/api/latex/generate", headers=auth_headers, json={
        "latexCode": SAFE_SOURCE,
        "jobDescription": "We need a software engineer with Python, Flask, React, testing, API design, clear communication, reliable delivery, and cross-functional collaboration.",
        "guardrails": ["single_page", "ats_safe"],
        "provider": "ollama",
        "model": "llama3.1:8b",
    })
    assert response.status_code == 200
    assert len(calls) == 2
    assert "complete LaTeX document" in calls[1]["compile_error"]
