from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)  # lifespan not triggered => no Mongo needed


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "MailSentinel AI"}


def test_health_db_reports_status_without_crashing():
    r = client.get("/health/db")
    assert r.status_code == 200
    assert r.json()["status"] in {"ok", "unavailable"}
