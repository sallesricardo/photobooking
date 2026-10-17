from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol


@dataclass(frozen=True)
class AvailabilitySlot:
    start: datetime
    end: datetime


class AgendaProvider(Protocol):
    """Abstração para qualquer agenda externa."""

    def list_available_slots(
        self,
        *,
        date: date,
        duration_minutes: int,
    ) -> list[AvailabilitySlot]:
        ...

    def cancel_booking(self, *, provider_event_id: str) -> None:
        ...

    def reschedule_booking(
        self,
        *,
        provider_event_id: str,
        new_start_at: datetime,
        duration_minutes: int,
    ) -> None:
        ...
