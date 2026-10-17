from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.metrics import RATE_LIMITED_TOTAL
from app.core.rate_limit import InMemoryRateLimiter, RateLimitExceeded, client_key


class RateLimitMiddleware:
    def __init__(self, app: ASGIApp, limit: int, window_seconds: int):
        self.app = app
        self.limiter = InMemoryRateLimiter(limit, window_seconds)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request
        request = Request(scope, receive=receive)
        key = f"{client_key(request)}:{scope.get('path', '')}"
        try:
            self.limiter.check(key)
        except RateLimitExceeded as exc:
            RATE_LIMITED_TOTAL.labels(path=scope.get("path", "unknown")).inc()
            response = JSONResponse(
                status_code=429,
                content={"detail": "Muitas requisições. Tente novamente mais tarde."},
                headers={"Retry-After": str(exc.retry_after)},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
