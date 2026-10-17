import os

import pytest

if not os.getenv("TEST_DATABASE_URL"):
    pytest.skip("Defina TEST_DATABASE_URL para executar os testes de integração.", allow_module_level=True)

os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]

from fastapi.testclient import TestClient
from app.main import app


pytestmark = pytest.mark.integration
client = TestClient(app)


def test_readiness_checks_postgresql():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
