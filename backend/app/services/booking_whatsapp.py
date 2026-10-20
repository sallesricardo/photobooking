"""Geração do link de WhatsApp a partir de uma reserva.

Extraído para que o fluxo de criação e o de reagendamento produzam sempre a
mesma mensagem: o link carrega a data/hora e precisa acompanhar o horário
atual da reserva.
"""

from datetime import datetime

from app.core.config import settings
from app.domain.agenda.timezones import strip_timezone
from app.services.whatsapp import WhatsAppService


def build_booking_whatsapp_url(
    *,
    session_name: str,
    package_name: str,
    price,
    start_at: datetime,
) -> str:
    """Monta o link `wa.me` com a mensagem da reserva.

    O horário é convertido para a hora de parede local (sem offset), que é o
    que o cliente espera ler: "para o dia 25/11/2026 às 14:00".
    """
    whatsapp = WhatsAppService(settings.whatsapp_phone)
    message = whatsapp.build_booking_message(
        session_name=session_name,
        package_name=package_name,
        price=price,
        start_at=strip_timezone(start_at),
    )
    return whatsapp.build_url(message)
