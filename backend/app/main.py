import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.google import router as google_router
from app.api.admin_bookings import router as admin_bookings_router
from app.api.sessions import router as sessions_router
from app.core.health import check_database
from app.core.logging import configure_logging, request_id_ctx
from app.core.request_id import RequestIdMiddleware

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PhotoBooking API",
    version="0.6.0",
    description="API demonstrativa para catálogo e agendamento de ensaios fotográficos.",
)

app.add_middleware(RequestIdMiddleware)

# origins = ["http://localhost:3000"]
origins = ["*"]

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
