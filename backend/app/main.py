import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.google import router as google_router
from app.api.admin_bookings import router as admin_bookings_router
from app.api.sessions import router as sessions_router
from app.core.health import check_database
from app.core.logging import configure_logging, request_id_ctx
from app.core.request_id import RequestIdMiddleware
from app.core.metrics_middleware import MetricsMiddleware
from app.core.rate_limit_middleware import RateLimitMiddleware
from app.core.config import settings

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PhotoBooking API",
    version="0.7.0",
    description="API demonstrativa para catálogo e agendamento de ensaios fotográficos.",
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(MetricsMiddleware)
if settings.rate_limit_enabled:
    app.add_middleware(
        RateLimitMiddleware,
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

# O frontend consome a API via BFF (mesma origem), então o backend quase
# nunca é acessado direto pelo navegador. Mantemos CORS restrito à origem
# configurada em FRONTEND_ORIGIN para casos de acesso direto (ex.: debugging).
origins = [origin.strip() for origin in settings.frontend_origin.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")
app.include_router(google_router, prefix="/api/v1")
app.include_router(admin_bookings_router, prefix="/api/v1")

# Prometheus exposition endpoint. In production, restrict this endpoint at the reverse proxy/network layer.
app.mount("/metrics", make_asgi_app())


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("request_validation_failed path=%s errors=%s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "request_id": request_id_ctx.get()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception method=%s path=%s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor.", "request_id": request_id_ctx.get()},
    )


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    try:
        check_database()
    except Exception:
        logger.exception("readiness_check_failed")
        return JSONResponse(status_code=503, content={"status": "not_ready", "database": "unavailable"})
    return {"status": "ok", "database": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1")
def api_root() -> dict[str, str]:
    return {"name": "PhotoBooking API", "version": "v1"}
