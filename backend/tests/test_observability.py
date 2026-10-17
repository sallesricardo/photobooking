from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_request_id_is_returned_and_preserved():
    response = client.get("/health/live", headers={"X-Request-ID": "portfolio-test-123"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "portfolio-test-123"


def test_request_id_is_generated_when_missing():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert len(response.headers["X-Request-ID"]) == 36
