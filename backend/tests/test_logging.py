from pathlib import Path


def test_requests_are_logged_with_a_visible_request_id(app, client):
    response = client.get("/api/health", headers={"X-Request-ID": "test-request-123"})
    for handler in app.logger.handlers:
        handler.flush()

    log_text = Path(app.config["LOG_FILE"]).read_text()
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"
    assert "[test-request-123]" in log_text
    assert "request.start method=GET path=/api/health" in log_text
    assert "request.end method=GET path=/api/health status=200" in log_text
    assert "accessToken" not in log_text


def test_latex_source_content_is_not_written_to_logs(app, client, auth_headers):
    private_marker = "private-resume-marker"
    response = client.post("/api/latex/compile", headers=auth_headers, json={
        "latexCode": rf"\documentclass{{article}}\input{{{private_marker}}}\begin{{document}}x\end{{document}}",
    })
    for handler in app.logger.handlers:
        handler.flush()

    log_text = Path(app.config["LOG_FILE"]).read_text()
    assert response.status_code == 400
    assert "error_code=unsafe_command" in log_text
    assert private_marker not in log_text
