import io


def test_resume_versions_and_analysis(client, auth_headers):
    first = client.post(
        "/api/resumes",
        headers=auth_headers,
        data={
            "name": "Backend resume",
            "category": "Engineering",
            "file": (io.BytesIO(b"Experience\nBuilt Flask APIs and improved latency by 35%.\nEducation\nSkills Python SQL"), "resume.txt"),
        },
        content_type="multipart/form-data",
    )
    assert first.status_code == 201
    resume = first.get_json()["resume"]

    second = client.post(
        f"/api/resumes/{resume['id']}/versions",
        headers=auth_headers,
        data={
            "notes": "Added database work",
            "file": (io.BytesIO(b"Experience\nBuilt Flask APIs with Python and PostgreSQL. Reduced latency 35%.\nEducation\nSkills"), "resume-v2.txt"),
        },
        content_type="multipart/form-data",
    )
    assert second.status_code == 201
    assert second.get_json()["resume"]["latestVersion"] == 2

    version_id = second.get_json()["resume"]["versions"][0]["id"]
    analysis = client.post("/api/applications/analyze", headers=auth_headers, json={
        "resumeVersionId": version_id,
        "companyName": "Acme",
        "roleTitle": "Backend Engineer",
        "jobDescription": "We need a backend engineer with strong Python, Flask, PostgreSQL, API design, testing, cloud deployment, and collaboration experience. You will build reliable services and improve latency.",
    })
    assert analysis.status_code == 201
    metrics = analysis.get_json()["application"]["metrics"]
    assert 0 <= metrics["overall"] <= 100
    assert "python" in metrics["matchedKeywords"]


def test_requires_owned_resume_version(client, auth_headers):
    response = client.post("/api/applications/analyze", headers=auth_headers, json={
        "resumeVersionId": 999,
        "jobDescription": "A sufficiently long job description that should not be reached because the selected resume does not exist for this signed-in user account."
    })
    assert response.status_code == 400

