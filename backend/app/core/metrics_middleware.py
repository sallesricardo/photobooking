import re
import time

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.metrics import REQUESTS_TOTAL, REQUEST_DURATION

_NUMERIC_SEGMENT = re.compile(r"^\d+$")
_UUID_SEGMENT = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}$")


def metric_path(path: str) -> str:
    """Reduce metric cardinality by replacing obvious resource IDs."""
    parts = path.split("/")
    normalized = []
    for part in parts:
        if _NUMERIC_SEGMENT.match(part) or _UUID_SEGMENT.match(part):
            normalized.append(":id")
        else:
            normalized.append(part)
    return "/".join(normalized) or "/"


class MetricsMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status = 500
        path = metric_path(scope.get("path", "unknown"))
        method = scope.get("method", "unknown")

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.perf_counter() - start
            REQUESTS_TOTAL.labels(method=method, path=path, status=str(status)).inc()
            REQUEST_DURATION.labels(method=method, path=path).observe(duration)
