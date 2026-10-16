from datetime import datetime
from decimal import Decimal
from urllib.parse import quote


class WhatsAppService:
    def __init__(self, phone_number: str) -> None:
        self.phone_number = phone_number

    def build_booking_message(
        self,
        *,
        session_name: str,
        package_name: str,
        price: Decimal,
        start_at: datetime,
    ) -> str:
        formatted_price = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        formatted_date = start_at.strftime("%d/%m/%Y")
        formatted_time = start_at.strftime("%H:%M")
        return (
            f"Olá! Quero agendar o {session_name}, no pacote {package_name}, "
            f"no valor de {formatted_price}, para o dia {formatted_date} às {formatted_time}."
        )

    def build_url(self, message: str) -> str:
        return f"https://wa.me/{self.phone_number}?text={quote(message)}"
