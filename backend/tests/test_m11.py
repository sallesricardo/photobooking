import time

from fastapi.testclient import TestClient

from app.core.rate_limit import InMemoryRateLimiter, RateLimitExceeded
from app.main import app


def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
    limiter.check("client")
    limiter.check("client")
    try:
        limiter.check("client")
    except RateLimitExceeded as exc:
        assert exc.retry_after >= 1
    else:
        raise AssertionError("expected rate limit")


def test_rate_limiter_expires_window():
    limiter = InMemoryRateLimiter(limit=1, window_seconds=1)
    limiter.check("client")
    try:
        limiter.check("client")
    except RateLimitExceeded:
        pass
    else:
        raise AssertionError("expected rate limit")
    time.sleep(1.05)
    limiter.check("client")


def test_metrics_endpoint_is_available():
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "photobooking_http_requests_total" in response.text
