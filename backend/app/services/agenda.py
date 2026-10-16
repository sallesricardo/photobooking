from datetime import date

from app.domain.agenda import AgendaProvider, AvailabilitySlot


class AgendaService:
    def __init__(self, provider: AgendaProvider) -> None:
        self.provider = provider

    def available_slots(self, *, target_date: date, duration_minutes: int) -> list[AvailabilitySlot]:
        return self.provider.list_available_slots(
            date=target_date,
            duration_minutes=duration_minutes,
        )
