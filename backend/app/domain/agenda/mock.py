from datetime import date, datetime, time, timedelta

from app.domain.agenda.provider import AgendaProvider, AvailabilitySlot


class MockAgendaProvider(AgendaProvider):
    """Provider local usado no desenvolvimento e na demonstração do projeto."""

    def __init__(self, *, slot_interval_minutes: int = 30) -> None:
        self.slot_interval_minutes = slot_interval_minutes

    def list_available_slots(
        self,
        *,
        date: date,
        duration_minutes: int,
    ) -> list[AvailabilitySlot]:
        if date < datetime.now().date():
            return []

        # Simula uma agenda com alguns horários ocupados.
        occupied = {time(12, 0), time(15, 0)}
        opening = datetime.combine(date, time(9, 0))
        closing = datetime.combine(date, time(18, 0))
        duration = timedelta(minutes=duration_minutes)
        step = timedelta(minutes=self.slot_interval_minutes)

        slots: list[AvailabilitySlot] = []
        current = opening
        while current + duration <= closing:
            if current.time() not in occupied:
                slots.append(
                    AvailabilitySlot(start=current, end=current + duration)
                )
            current += step

        return slots
