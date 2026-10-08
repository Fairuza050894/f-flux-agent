"""Regression safety tests for PATCH-001: Baseline, Safety Net & API Contract."""

from collections import Counter
from pathlib import Path
import os
import pytest
from fastapi.testclient import TestClient

from qa_dashboard.backend.app import (
    ROOT,
    QA_ARTIFACT_ROOT,
    app,
    get_cors_origins,
    _qa_mask_sensitive_headers,
    _qa_mask_sensitive_text,
)
from qa_dashboard.backend.execution_store import (
    sanitize_value,
    is_sensitive_key,
    read_store,
)


@pytest.fixture
def client():
    """Test client fixture for the FastAPI dashboard application."""
    return TestClient(app)


# 1. Health endpoint
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "Hermes QA Dashboard API"
    assert "root" in data
    assert "default_base_url" in data


# 2. No duplicate HTTP method/path registrations
def test_no_duplicate_route_registrations():
    route_methods = []
    for route in app.routes:
        methods = getattr(route, "methods", None) or ["GET"]
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            route_methods.append((route.path, method))

    counts = Counter(route_methods)
    duplicates = [item for item, count in counts.items() if count > 1]
    assert duplicates == [], f"Found duplicate route registrations: {duplicates}"


# 3. Canonical run lifecycle route (/api/v1/runs)
def test_canonical_run_lifecycle_route(client, tmp_path, monkeypatch):
    test_store_path = tmp_path / "test_active_runs.json"
    import qa_dashboard.backend.execution_store as es
    monkeypatch.setattr(es, "STORE_PATH", test_store_path)

    payload = {
        "project_id": "test-project",
        "source": "ui_testing",
        "feature": "Smoke Test",
        "test_type": "ui",
        "environment": "staging",
        "request_snapshot": {"target_url": "https://example.com/test"},
    }
    response = client.post("/api/v1/runs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["project_id"] == "test-project"
    assert data["source"] == "ui_testing"
    assert data["feature"] == "Smoke Test"
    assert data["status"] == "queued"
    assert data["progress"] == 0


# 4. Registered/legacy run route does not collide
def test_registered_run_route_does_not_collide(client, monkeypatch):
    def mock_audit(url, module_name, mode):
        return {
            "status": "PASS",
            "testing_summary": "Mock audit passed",
            "standard_json_path": None,
        }

    monkeypatch.setattr("qa_dashboard.backend.app.perform_audit_for_telegram", mock_audit)

    payload = {
        "feature": "driver_daily_meal",
        "mode": "regression",
        "url": "https://example.com",
    }
    resp = client.post("/api/v1/registered-runs", json=payload)
    assert resp.status_code == 200
    assert resp.json().get("ok") is True
    assert resp.json().get("status") == "PASS"

    # Verify lifecycle route /api/v1/runs rejects this payload (missing project_id)
    lifecycle_resp = client.post("/api/v1/runs", json=payload)
    assert lifecycle_resp.status_code == 422

    # Verify invalid feature on registered-runs returns 400
    invalid_resp = client.post("/api/v1/registered-runs", json={"feature": "non_existent_feature"})
    assert invalid_resp.status_code == 400


# 5. Artifact valid path
def test_artifact_valid_path(client):
    test_artifact_dir = QA_ARTIFACT_ROOT / "reports"
    test_artifact_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_artifact_dir / "test_patch_001_valid_artifact.txt"
    test_file.write_text("VALID_ARTIFACT_CONTENT_PATCH_001", encoding="utf-8")

    try:
        # Relative path retrieval
        resp_rel = client.get("/api/v1/artifacts?path=reports/test_patch_001_valid_artifact.txt")
        assert resp_rel.status_code == 200
        assert resp_rel.text == "VALID_ARTIFACT_CONTENT_PATCH_001"

        # Absolute path retrieval inside artifact root
        resp_abs = client.get(f"/api/v1/artifacts?path={test_file}")
        assert resp_abs.status_code == 200
        assert resp_abs.text == "VALID_ARTIFACT_CONTENT_PATCH_001"

        # Legacy /artifacts route retrieval
        resp_legacy = client.get(f"/artifacts?path={test_file}")
        assert resp_legacy.status_code == 200
        assert resp_legacy.text == "VALID_ARTIFACT_CONTENT_PATCH_001"
    finally:
        if test_file.exists():
            test_file.unlink()


# 6. Artifact path traversal rejection
def test_artifact_path_traversal_rejection(client):
    traversal_paths = [
        "../../etc/passwd",
        "../pyproject.toml",
        "reports/../../pyproject.toml",
        "../../../etc/shadow",
        "....//....//etc/passwd",
    ]
    for path in traversal_paths:
        resp = client.get(f"/api/v1/artifacts?path={path}")
        assert resp.status_code in {403, 404}, f"Path {path} returned status {resp.status_code}"
        assert resp.status_code != 200


# 7. Repository file access rejection
def test_repository_file_access_rejection(client):
    sensitive_repo_files = [
        "pyproject.toml",
        "LICENSE",
        ".env",
        "qa_dashboard/backend/app.py",
        "qa_dashboard/backend/execution_store.py",
        str(ROOT / "pyproject.toml"),
        str(ROOT / "LICENSE"),
    ]
    for path in sensitive_repo_files:
        resp = client.get(f"/api/v1/artifacts?path={path}")
        assert resp.status_code in {403, 404}, f"Repo file {path} returned {resp.status_code}"
        assert resp.status_code != 200

        # Also verify unversioned /artifacts endpoint blocks it
        resp_legacy = client.get(f"/artifacts?path={path}")
        assert resp_legacy.status_code in {403, 404}
        assert resp_legacy.status_code != 200


# 8. Execution lifecycle happy path
def test_execution_lifecycle_happy_path(client, tmp_path, monkeypatch):
    test_store_path = tmp_path / "lifecycle_active_runs.json"
    import qa_dashboard.backend.execution_store as es
    monkeypatch.setattr(es, "STORE_PATH", test_store_path)

    # A. Create run
    create_payload = {
        "project_id": "proj-lifecycle",
        "source": "ui_testing",
        "feature": "Happy Path Test",
        "test_type": "ui",
        "environment": "qa-sandbox",
        "request_snapshot": {"step": "init"},
    }
    create_resp = client.post("/api/v1/runs", json=create_payload)
    assert create_resp.status_code == 200
    run_id = create_resp.json()["run_id"]
    assert run_id.startswith("run-")

    # B. List active runs - should include run_id
    active_resp = client.get("/api/v1/runs/active?project_id=proj-lifecycle")
    assert active_resp.status_code == 200
    active_runs = active_resp.json()["runs"]
    assert any(r["run_id"] == run_id for r in active_runs)

    # C. Update progress
    progress_payload = {
        "status": "running",
        "progress": 45.0,
        "current_stage": "execution",
        "current_step": "clicking button",
        "passed": 3,
        "failed": 0,
        "safe_metadata": {"browser": "chromium"},
    }
    prog_resp = client.patch(f"/api/v1/runs/{run_id}/progress", json=progress_payload)
    assert prog_resp.status_code == 200
    prog_data = prog_resp.json()
    assert prog_data["status"] == "running"
    assert prog_data["progress"] == 45.0
    assert prog_data["current_stage"] == "execution"
    assert prog_data["passed"] == 3

    # D. Complete run
    complete_payload = {
        "status": "completed",
        "progress": 100.0,
        "passed": 5,
        "failed": 0,
        "result_summary": {"notes": "all 5 assertions passed"},
    }
    comp_resp = client.post(f"/api/v1/runs/{run_id}/complete", json=complete_payload)
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert comp_data["status"] == "completed"
    assert comp_data["progress"] == 100.0

    # E. Active runs should no longer contain completed run
    active_resp2 = client.get("/api/v1/runs/active?project_id=proj-lifecycle")
    assert active_resp2.status_code == 200
    assert not any(r["run_id"] == run_id for r in active_resp2.json()["runs"])

    # F. Fetch by run_id
    get_resp = client.get(f"/api/v1/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "completed"


# 9. Sensitive information redaction
def test_sensitive_information_redaction():
    sensitive_dict = {
        "user": "alice",
        "password": "super-secret-password",
        "api_key": "sk-1234567890abcdef",
        "nested": {
            "token": "bearer-token-val",
            "safe_field": "safe_value",
            "authorization": "Basic dXNlcjpwYXNz",
        },
        "items": [
            {"secret": "my-secret"},
            {"safe": 42},
        ],
    }
    sanitized = sanitize_value(sensitive_dict)
    assert sanitized["user"] == "alice"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["authorization"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == "safe_value"
    assert sanitized["items"][0]["secret"] == "[REDACTED]"
    assert sanitized["items"][1]["safe"] == 42

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer my_secret_token",
        "X-Api-Key": "secret-api-key",
        "Cookie": "session=xyz123",
        "Accept": "text/html",
    }
    masked_headers = _qa_mask_sensitive_headers(headers)
    assert masked_headers["Content-Type"] == "application/json"
    assert masked_headers["Authorization"] == "***MASKED***"
    assert masked_headers["X-Api-Key"] == "***MASKED***"
    assert masked_headers["Cookie"] == "***MASKED***"
    assert masked_headers["Accept"] == "text/html"

    raw_text = "Sending Bearer eyJhbGciOi... with password=myPassword123 and token: myToken456"
    masked_text = _qa_mask_sensitive_text(raw_text)
    assert "myPassword123" not in masked_text
    assert "myToken456" not in masked_text
    assert "***MASKED***" in masked_text
