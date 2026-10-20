"""Testes de integração da API de agendamento, cobrindo os dois providers.

Estes testes exercitam o caminho real (HTTP -> API -> provider) e protegem
contra regressões de contrato entre a API, o mock e o Google Calendar.
"""

import json
import os
import urllib.parse
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.booking import Booking
from app.models.package import SessionPackage
from app.models.session import PhotographySession


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Cliente de teste com um banco SQLite isolado e catálogo populado."""
    db_path = Path(tmp_path) / "test.db"
    url = f"sqlite:///{db_path}"

    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def _fk(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with TestingSession() as db:
        session = PhotographySession(slug="feminino", name="Ensaio Feminino", description="Teste")
        session.packages.append(
            SessionPackage(name="Essencial", description="60 min", price=450, duration_minutes=60, display_order=0)
        )
        db.add(session)
        db.commit()

    # O app usa o engine global; apontamos para o banco isolado.
    import app.db.session as db_session

    monkeypatch.setattr(db_session, "engine", engine)
    monkeypatch.setattr(db_session, "SessionLocal", TestingSession)
    monkeypatch.setattr("app.api.dependencies.get_db", lambda: iter([db_session.SessionLocal()]))
    monkeypatch.setattr("app.repositories.booking.SessionLocal", TestingSession, raising=False)
    monkeypatch.setattr("app.core.health.engine", engine, raising=False)

    from app.main import app

    with TestClient(app) as test_client:
        yield test_client


def _availability(client, target_date="2026-10-20"):
    response = client.get(
        "/api/v1/booking/availability",
        params={"session_slug": "feminino", "package_id": 1, "target_date": target_date},
    )
    assert response.status_code == 200, response.text
    return response.json()["slots"]


def test_availability_returns_slots_for_the_mock_provider(client):
    slots = _availability(client)
    assert len(slots) > 0
    assert slots[0].startswith("2026-10-20T")


def test_booking_accepts_the_slot_returned_by_availability(client):
    """Regressão: o cliente ecoa o slot do availability no booking."""
    slot = _availability(client)[0]

    response = client.post(
        "/api/v1/booking/whatsapp",
        headers={"Idempotency-Key": "test-availability-1"},
        json={"session_slug": "feminino", "package_id": 1, "start_at": slot},
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "confirmed"


def test_booking_is_idempotent_with_the_same_key(client):
    slot = _availability(client)[0]
    payload = {"session_slug": "feminino", "package_id": 1, "start_at": slot}

    first = client.post("/api/v1/booking/whatsapp", headers={"Idempotency-Key": "test-idem-1"}, json=payload)
    second = client.post("/api/v1/booking/whatsapp", headers={"Idempotency-Key": "test-idem-1"}, json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_booking_rejects_a_time_outside_the_available_slots(client):
    response = client.post(
        "/api/v1/booking/whatsapp",
        headers={"Idempotency-Key": "test-invalid-1"},
        json={"session_slug": "feminino", "package_id": 1, "start_at": "2026-10-20T03:00:00"},
    )

    assert response.status_code == 409


def test_google_provider_is_usable_through_the_api(client, monkeypatch):
    """O Google Calendar precisa funcionar pelo mesmo caminho público da API.

    Regressão de contrato: o provider declarava `target_date=` enquanto a API
    chamava `date=`, o que derrubava toda a integração com 502.
    """
    from app.integrations.google.calendar import GoogleCalendarProvider

    created_events = []

    class FakeFreeBusy:
        def query(self, **kwargs):
            class Request:
                def execute(self):
                    return {"calendars": {}}

            return Request()

    class FakeEvents:
        def list(self, **kwargs):
            class Request:
                def execute(self):
                    return {"items": []}

            return Request()

        def insert(self, **kwargs):
            created_events.append(kwargs.get("body", {}))

            class Request:
                def execute(self):
                    return {"id": "evt-test-1"}

            return Request()

    class FakeService:
        def freebusy(self):
            return FakeFreeBusy()

        def events(self):
            return FakeEvents()

    monkeypatch.setattr(GoogleCalendarProvider, "_service", lambda self: FakeService())
    monkeypatch.setattr("app.core.config.settings.calendar_provider", "google")

    slots = _availability(client)
    assert slots, "o provider google deve devolver slots"
    # O Google devolve datetimes aware no fuso da aplicação.
    assert slots[0].endswith("-03:00") or slots[0].endswith("+00:00")

    response = client.post(
        "/api/v1/booking/whatsapp",
        headers={"Idempotency-Key": "test-google-1"},
        json={"session_slug": "feminino", "package_id": 1, "start_at": slots[0]},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["provider"] == "google"
    assert body["calendar_event_id"] == "evt-test-1"

    # O evento foi criado com o horário e a chave de idempotência corretos.
    assert created_events, "o evento deveria ter sido criado no Google Calendar"
    assert created_events[0]["extendedProperties"]["private"]["photobooking_idempotency_key"] == "test-google-1"


def test_google_provider_without_credentials_returns_503(client, monkeypatch):
    """Sem credenciais, o erro deve ser 503 com mensagem útil (não 502 genérico)."""
    from app.integrations.google.calendar import GoogleCalendarNotConfigured, GoogleCalendarProvider

    def raise_not_configured(self):
        raise GoogleCalendarNotConfigured("Google Calendar não está conectado.")

    monkeypatch.setattr(GoogleCalendarProvider, "_service", raise_not_configured)
    monkeypatch.setattr("app.core.config.settings.calendar_provider", "google")

    response = client.get(
        "/api/v1/booking/availability",
        params={"session_slug": "feminino", "package_id": 1, "target_date": "2026-10-20"},
    )

    assert response.status_code == 503
    assert "conectado" in response.json()["detail"]


def test_reschedule_accepts_local_wall_clock_time(client):
    """O admin envia a hora local chosen no formulário (sem offset)."""
    slot = _availability(client)[0]
    client.post(
        "/api/v1/booking/whatsapp",
        headers={"Idempotency-Key": "test-reschedule-1"},
        json={"session_slug": "feminino", "package_id": 1, "start_at": slot},
    )

    client.post("/api/v1/auth/login", json={"username": "admin", "password": "change-me-admin"})

    response = client.post(
        "/api/v1/admin/bookings/1/reschedule",
        json={"start_at": "2026-10-21T10:00:00"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["start_at"].startswith("2026-10-21T10:00:00")


def test_reschedule_updates_the_whatsapp_message(client):
    """Regressão: o link do WhatsApp carregava o horário antigo do booking."""
    slot = _availability(client)[0]
    client.post(
        "/api/v1/booking/whatsapp",
        headers={"Idempotency-Key": "test-whatsapp-1"},
        json={"session_slug": "feminino", "package_id": 1, "start_at": slot},
    )

    client.post("/api/v1/auth/login", json={"username": "admin", "password": "change-me-admin"})

    response = client.post(
        "/api/v1/admin/bookings/1/reschedule",
        json={"start_at": "2026-10-21T10:00:00"},
    )
    assert response.status_code == 200, response.text

    message = urllib.parse.unquote(response.json()["whatsapp_url"].split("text=")[1])
    assert "21/10/2026" in message
    assert "10:00" in message
    # O horário antigo não pode sobrar na mensagem.
    assert "20/10/2026" not in message
