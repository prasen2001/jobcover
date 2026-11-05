def test_signup_login_and_profile(client):
    signup = client.post("/api/auth/signup", json={
        "fullName": "Alex Morgan",
        "email": "alex@example.com",
        "password": "correct-horse",
    })
    assert signup.status_code == 201
    token = signup.get_json()["accessToken"]

    duplicate = client.post("/api/auth/signup", json={
        "email": "alex@example.com", "password": "correct-horse"
    })
    assert duplicate.status_code == 409

    login = client.post("/api/auth/login", json={
        "email": "alex@example.com", "password": "correct-horse"
    })
    assert login.status_code == 200

    saved = client.put("/api/profile", headers={"Authorization": f"Bearer {token}"}, json={
        "collegeName": "State University",
        "degreeName": "Bachelor of Science",
        "programName": "Computer Science",
        "enrollmentYear": 2021,
        "graduationYear": 2025,
        "skills": "Python, Flask, React",
    })
    assert saved.status_code == 200
    assert saved.get_json()["profile"]["collegeName"] == "State University"
    assert saved.get_json()["profile"]["degreeName"] == "Bachelor of Science"
    assert saved.get_json()["profile"]["programName"] == "Computer Science"


def test_rejects_short_password(client):
    response = client.post("/api/auth/signup", json={
        "email": "alex@example.com", "password": "short"
    })
    assert response.status_code == 400

