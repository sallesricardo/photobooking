from datetime import date, datetime
from types import SimpleNamespace

from app.integrations.google.calendar import GoogleCalendarProvider


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
        target_date=date(2026, 10, 20),
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
