from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PhotoBooking API",
    version="0.1.0",
    description="API demonstrativa para agendamento de ensaios fotográficos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1")
def api_root() -> dict[str, str]:
    return {"name": "PhotoBooking API", "version": "v1"}
