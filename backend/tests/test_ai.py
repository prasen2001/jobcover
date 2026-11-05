import pytest

from app.services.ai import generate_cover_letter


BASE_ARGS = {
    "profile": {"fullName": "Alex Morgan", "skills": "Python and React"},
    "resume_text": "Built reliable Python services and React interfaces.",
    "job_text": "Seeking an engineer with Python and React experience.",
    "company": "Acme",
    "role": "Software Engineer",
    "metrics": {"matchedKeywords": ["python", "react"]},
}


def test_rejects_unapproved_provider():
    with pytest.raises(ValueError, match="gemini or groq"):
        generate_cover_letter(**BASE_ARGS, provider="untrusted-provider")


def test_explicit_gemini_requires_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GOOGLE_API_KEY"):
        generate_cover_letter(
            **BASE_ARGS,
            provider="gemini",
            model_name="gemini-3.8-flash",
        )


def test_rejects_unapproved_model(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    with pytest.raises(ValueError, match="not allowed"):
        generate_cover_letter(
            **BASE_ARGS,
            provider="gemini",
            model_name="gemini-unknown",
        )
