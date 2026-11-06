import pytest

from app.services.latex_resume import (
    LatexValidationError,
    _extract_latex,
    validate_guardrails,
    validate_grounded_facts,
    validate_latex_source,
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


def test_rejects_new_numeric_claims_from_generated_resume():
    generated = SAFE_SOURCE.replace("Python experience", "Python experience that improved revenue by 42%")
    with pytest.raises(LatexValidationError, match="unsupported number"):
        validate_grounded_facts(SAFE_SOURCE, generated, {"fullName": "Alex Morgan"})


def test_accepts_numbers_already_supported_by_source():
    source = SAFE_SOURCE.replace("Python experience", "Python experience that improved latency by 35%")
    validate_grounded_facts(source, source, {"fullName": "Alex Morgan"})


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


def test_compile_route_returns_pdf_payload(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.routes.latex.compile_latex",
        lambda source, **kwargs: {"latexCode": source.strip(), "pdfBase64": "JVBERi0=", "pageCount": 1},
    )
    response = client.post("/api/latex/compile", headers=auth_headers, json={"latexCode": SAFE_SOURCE})
    assert response.status_code == 200
    assert response.get_json()["pageCount"] == 1


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
