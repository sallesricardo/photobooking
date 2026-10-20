import inspect
from datetime import date, datetime
from types import SimpleNamespace

import pytest
from googleapiclient.errors import HttpError

from app.domain.agenda.mock import MockAgendaProvider
from app.domain.agenda.provider import AgendaProvider
from app.integrations.google.calendar import GoogleCalendarProvider
from app.services.agenda import AgendaService


def test_providers_satisfy_the_agenda_provider_contract():
    """Todos os providers precisam ter a MESMA assinatura do protocolo.

    Sem este teste, um provider pode divergir no nome do parâmetro (ex.:
    `target_date=` em vez de `date=`) e falhar com TypeError em runtime,
    enquanto a suíte continua verde por só chamar o provider diretamente.
    """
    expected = set(inspect.signature(AgendaProvider.list_available_slots).parameters) - {"self"}

    for provider_class in (MockAgendaProvider, GoogleCalendarProvider):
        actual = set(inspect.signature(provider_class.list_available_slots).parameters) - {"self"}
        assert expected.issubset(actual), (
            f"{provider_class.__name__}.list_available_slots não implementa o "
            f"AgendaProvider: esperado {sorted(expected)}, encontrado {sorted(actual)}"
        )


def test_agenda_service_calls_providers_with_protocol_signature(monkeypatch):
    """O AgendaService passa `date=`; o provider precisa aceitar esse nome."""
    provider = GoogleCalendarProvider()
    captured = {}

    def fake_slots(*, date, duration_minutes, **kwargs):
        captured["date"] = date
        captured["duration_minutes"] = duration_minutes
        return []

    monkeypatch.setattr(provider, "list_available_slots", fake_slots)

    AgendaService(provider).available_slots(
        target_date=date(2026, 10, 20), duration_minutes=60
    )

    assert captured == {"date": date(2026, 10, 20), "duration_minutes": 60}


def test_available_slots_are_generated_from_freebusy(monkeypatch):
    provider = GoogleCalendarProvider()

    class FakeRequest:
        def execute(self):
            return {
                "calendars": {
                    provider.calendar_id: {
                        "busy": [
                            {
                                "start": "2026-10-20T10:00:00-03:00",
                                "end": "2026-10-20T11:00:00-03:00",
                            }
                        ]
                    }
                }
            }

    class FakeFreeBusy:
        def query(self, **kwargs):
            return FakeRequest()

    fake_service = SimpleNamespace(freebusy=lambda: FakeFreeBusy())
    monkeypatch.setattr(provider, "_service", lambda: fake_service)

    slots = provider.list_available_slots(
        date=date(2026, 10, 20),
        duration_minutes=60,
        opening_hour=9,
        closing_hour=12,
        slot_interval_minutes=60,
    )

    starts = [slot.start.hour for slot in slots]
    assert starts == [9, 11]


def test_naive_datetime_is_normalized_to_app_timezone():
    provider = GoogleCalendarProvider()
    value = provider._normalize_datetime(datetime(2026, 10, 20, 15, 30))
    assert value.tzinfo is not None
    assert value.hour == 15


def _http_error(status: int) -> HttpError:
    # `HttpError` lê `resp.reason` na inicialização (google-api-python-client
    # >= 2.201), então a resposta falsa precisa ter esse atributo.
    return HttpError(SimpleNamespace(status=status, reason="Service Unavailable"), b"error")


def test_create_booking_recovers_existing_event_by_idempotency_key(monkeypatch):
    provider = GoogleCalendarProvider()
    calls = {"insert": 0}

    class FakeRequest:
        def execute(self):
            return {"items": [{"id": "evt-existing"}]}

    class FakeEvents:
        def list(self, **kwargs):
            assert kwargs["privateExtendedProperty"] == ["photobooking_idempotency_key=req-123"]
            return FakeRequest()

        def insert(self, **kwargs):
            calls["insert"] += 1
            return FakeRequest()

    fake_service = SimpleNamespace(events=lambda: FakeEvents())
    monkeypatch.setattr(provider, "_service", lambda: fake_service)

    event_id = provider.create_booking(
        start_at=datetime(2026, 10, 20, 15, 30),
        duration_minutes=60,
        title="Ensaio Família - Premium",
        description="demo",
        idempotency_key="req-123",
    )

    assert event_id == "evt-existing"
    assert calls["insert"] == 0


def test_transient_freebusy_error_is_retried(monkeypatch):
    provider = GoogleCalendarProvider()
    attempts = {"count": 0}

    class FakeRequest:
        def execute(self):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise _http_error(503)
            return {"calendars": {provider.calendar_id: {"busy": []}}}

    class FakeFreeBusy:
        def query(self, **kwargs):
            return FakeRequest()

    fake_service = SimpleNamespace(freebusy=lambda: FakeFreeBusy())
    monkeypatch.setattr(provider, "_service", lambda: fake_service)
    monkeypatch.setattr("time.sleep", lambda _: None)

    slots = provider.list_available_slots(
        date=date(2026, 10, 20),
        duration_minutes=60,
        opening_hour=9,
        closing_hour=10,
        slot_interval_minutes=60,
    )

    assert attempts["count"] == 3
    assert len(slots) == 1


def test_transient_insert_error_is_not_retried(monkeypatch):
    provider = GoogleCalendarProvider()
    calls = {"insert": 0}

    class FakeRequest:
        def execute(self):
            return {"calendars": {provider.calendar_id: {"busy": []}}}

    class FakeFreeBusy:
        def query(self, **kwargs):
            return FakeRequest()

    class FakeInsertRequest:
        def execute(self):
            calls["insert"] += 1
            raise _http_error(503)

    class FakeEvents:
        def list(self, **kwargs):
            class Empty:
                def execute(self):
                    return {"items": []}
            return Empty()

        def insert(self, **kwargs):
            return FakeInsertRequest()

    fake_service = SimpleNamespace(
        freebusy=lambda: FakeFreeBusy(),
        events=lambda: FakeEvents(),
    )
    monkeypatch.setattr(provider, "_service", lambda: fake_service)

    with pytest.raises(RuntimeError, match="temporariamente indisponível"):
        provider.create_booking(
            start_at=datetime(2026, 10, 20, 15, 30),
            duration_minutes=60,
            title="Ensaio",
            description="demo",
            idempotency_key="req-456",
        )

    assert calls["insert"] == 1
