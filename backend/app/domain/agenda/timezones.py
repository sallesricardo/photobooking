"""Normalização de horários entre a API e os providers de agenda.

Os providers não falam o mesmo "dialeto" de timezone:

- ``MockAgendaProvider`` devolve datetimes *naive* (a hora de parede local).
- ``GoogleCalendarProvider`` devolve datetimes *aware* em ``APP_TIMEZONE``.

O cliente (frontend) trabalha com a hora de parede que o usuário escolheu no
formulário, e a recebe de volta em um dos dois formatos. Para que a comparação
"o horário pedido está entre os slots?" funcione em ambos os casos, a API
normaliza a entrada para o mesmo dialeto do provider antes de comparar.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings


def app_timezone() -> ZoneInfo:
    """Fuso horário configurado da aplicação."""
    return ZoneInfo(settings.app_timezone)


def to_app_timezone(value: datetime) -> datetime:
    """Interpreta a hora de parede local como sendo no fuso da aplicação.

    Naive  -> presume que o usuário digitou no fuso da aplicação.
    Aware  -> converte para o fuso da aplicação.
    """
    tz = app_timezone()
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def strip_timezone(value: datetime) -> datetime:
    """Remove o offset, preservando a hora de parede local."""
    if value.tzinfo is None:
        return value
    return value.astimezone(app_timezone()).replace(tzinfo=None)


def matches_slot(requested: datetime, slot_start: datetime) -> bool:
    """Compara o horário pedido com o início de um slot.

    A comparação é feita na hora de parede local, para que funcione tanto
    para datetimes naive (mock) quanto aware (Google Calendar).
    """
    return strip_timezone(requested) == strip_timezone(slot_start)
