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


def test_cover_letter_streams_words_and_saves_result(client, auth_headers, monkeypatch):
    uploaded = client.post(
        "/api/resumes",
        headers=auth_headers,
        data={
            "name": "Engineering resume",
            "category": "Engineering",
            "file": (io.BytesIO(b"Python Flask React experience"), "resume.txt"),
        },
        content_type="multipart/form-data",
    ).get_json()["resume"]
    version_id = uploaded["versions"][0]["id"]
    analyzed = client.post("/api/applications/analyze", headers=auth_headers, json={
        "resumeVersionId": version_id,
        "companyName": "Acme",
        "roleTitle": "Engineer",
        "jobDescription": "We need an engineer with Python, Flask, React, API design, testing, deployment, ownership, communication, and strong collaboration experience.",
    }).get_json()["application"]
    monkeypatch.setattr(
        "app.routes.applications.stream_cover_letter",
        lambda *args, **kwargs: iter(["Dear ", "Hiring ", "Team"]),
    )

    response = client.post(
        f"/api/applications/{analyzed['id']}/cover-letter/stream",
        headers=auth_headers,
        json={"provider": "ollama", "model": "llama3.1:8b"},
    )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert body.count('"type": "token"') == 3
    assert '"type": "done"' in body
    saved = client.get("/api/applications", headers=auth_headers).get_json()["applications"][0]
    assert saved["coverLetter"] == "Dear Hiring Team"

