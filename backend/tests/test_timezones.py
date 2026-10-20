"""Normalização de timezone entre a API e os providers de agenda.

O mock devolve datetimes naive e o Google Calendar devolve datetimes aware.
A API precisa comparar os dois corretamente, senão todo horário vira 409.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.domain.agenda.mock import MockAgendaProvider
from app.domain.agenda.timezones import matches_slot, strip_timezone, to_app_timezone

TZ = ZoneInfo("America/Sao_Paulo")


def test_naive_datetime_is_assumed_to_be_in_app_timezone():
    result = to_app_timezone(datetime(2026, 10, 20, 9, 0))
    assert result.tzinfo is not None
    assert result.hour == 9
    assert result.utcoffset() == datetime(2026, 10, 20, 9, 0, tzinfo=TZ).utcoffset()


def test_aware_datetime_is_converted_to_app_timezone():
    utc_value = datetime(2026, 10, 20, 12, 0, tzinfo=ZoneInfo("UTC"))
    result = to_app_timezone(utc_value)
    assert result.hour == 9
    assert result.utcoffset() == datetime(2026, 10, 20, 9, 0, tzinfo=TZ).utcoffset()


def test_google_slot_survives_normalization_unchanged():
    """O slot do Google (aware) não pode ser deslocado pela normalização."""
    google_slot = datetime(2026, 10, 20, 9, 0, tzinfo=TZ)
    assert to_app_timezone(google_slot) == google_slot


def test_slot_matches_naive_and_aware_requests():
    google_slot = datetime(2026, 10, 20, 9, 0, tzinfo=TZ)
    mock_slot = datetime(2026, 10, 20, 9, 0)

    naive_request = datetime(2026, 10, 20, 9, 0)
    aware_request = google_slot

    assert matches_slot(naive_request, google_slot)
    assert matches_slot(aware_request, google_slot)
    assert matches_slot(naive_request, mock_slot)
    assert matches_slot(aware_request, mock_slot)


def test_different_wall_clock_times_do_not_match():
    google_slot = datetime(2026, 10, 20, 9, 0, tzinfo=TZ)
    assert not matches_slot(datetime(2026, 10, 20, 10, 0), google_slot)
    assert not matches_slot(datetime(2026, 10, 21, 9, 0), google_slot)


def test_strip_timezone_keeps_wall_clock_time():
    assert strip_timezone(datetime(2026, 10, 20, 9, 0, tzinfo=TZ)) == datetime(2026, 10, 20, 9, 0)
    assert strip_timezone(datetime(2026, 10, 20, 9, 0)) == datetime(2026, 10, 20, 9, 0)


def test_mock_provider_slots_match_the_normalized_request():
    """O fluxo do cliente: availability devolve naive -> booking com esse valor."""
    provider = MockAgendaProvider()
    slots = provider.list_available_slots(date=date(2026, 10, 20), duration_minutes=60)
    assert slots, "o mock deve devolver slots para uma data futura"

    requested = to_app_timezone(slots[0].start)
    assert any(matches_slot(requested, slot.start) for slot in slots)
