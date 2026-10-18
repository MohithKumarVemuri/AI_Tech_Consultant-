import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.db import init_db

# Initialize database tables for testing
init_db()

client = TestClient(app)

def test_health_check_endpoint():
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_query_auth_failure():
    resp = client.post("/v1/query", json={"question": "Test without key"})
    assert resp.status_code == 401

def test_query_successful_response():
    resp = client.post(
        "/v1/query",
        headers={"X-API-Key": settings.KB_API_KEY},
        json={"question": "How do I configure recurring membership billing?"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("answered", "insufficient_evidence")
    assert "sources" in data
    assert "request_id" in data

def test_escalation_flow():
    # 1. Create escalation
    create_resp = client.post(
        "/v1/escalations",
        headers={"X-API-Key": settings.KB_API_KEY},
        json={"question": "Can I integrate a custom quantum computer?"}
    )
    assert create_resp.status_code == 200
    esc_id = create_resp.json()["id"]

    # 2. List escalations
    list_resp = client.get(
        "/v1/escalations?status=open",
        headers={"X-API-Key": settings.KB_API_KEY}
    )
    assert list_resp.status_code == 200
    ids = [e["id"] for e in list_resp.json()]
    assert esc_id in ids

    # 3. Resolve escalation
    resolve_resp = client.post(
        f"/v1/escalations/{esc_id}/resolve",
        headers={"X-API-Key": settings.KB_API_KEY},
        json={
            "expert_answer": "Brilliant Directories operates on standard cloud infrastructure and does not natively support quantum computing interfaces.",
            "reviewer": "Tech Lead Sarah"
        }
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "resolved"
