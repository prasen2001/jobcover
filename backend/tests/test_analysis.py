from app.services.analysis import analyze_resume


def test_analysis_returns_explainable_dimensions():
    result = analyze_resume(
        "Experience: Built Python data pipelines. Improved throughput 40%. Skills: Python SQL. Education.",
        "Data engineer needed for Python, SQL, pipelines, AWS, testing, stakeholder communication and analytics.",
    )
    assert len(result["dimensions"]) == 5
    assert "python" in result["matchedKeywords"]
    assert "aws" in result["missingKeywords"]
    assert result["suggestions"]

