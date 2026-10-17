from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.google import router as google_router
from app.api.admin_bookings import router as admin_bookings_router
from app.api.sessions import router as sessions_router

app = FastAPI(
    title="PhotoBooking API",
    version="0.4.0",
    description="API demonstrativa para catálogo e agendamento de ensaios fotográficos.",
)

# origins = ["http://localhost:3000"]
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(booking_router, prefix="/api/v1")
app.include_router(google_router, prefix="/api/v1")
app.include_router(admin_bookings_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1")
def api_root() -> dict[str, str]:
    return {"name": "PhotoBooking API", "version": "v1"}
