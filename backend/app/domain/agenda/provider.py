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
