from datetime import datetime
from decimal import Decimal

from app.services.whatsapp import WhatsAppService


def test_build_booking_message_and_url():
    service = WhatsAppService("5511999999999")
    message = service.build_booking_message(
        session_name="Ensaio Família",
        package_name="Premium",
        price=Decimal("850.00"),
        start_at=datetime(2026, 10, 20, 15, 30),
    )

    assert "Ensaio Família" in message
    assert "Premium" in message
    assert "R$ 850,00" in message
    assert "20/10/2026" in message
    assert service.build_url(message).startswith("https://wa.me/5511999999999?text=")
