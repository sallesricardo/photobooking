from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.core.config import settings
from app.domain.agenda import MockAgendaProvider
from app.integrations.google.calendar import GoogleCalendarNotConfigured, GoogleCalendarProvider
from app.repositories.session import SessionRepository
from app.services.agenda import AgendaService
from app.services.whatsapp import WhatsAppService

router = APIRouter(prefix="/booking", tags=["booking"])


class AvailabilityResponse(BaseModel):
    date: date
    provider: str
    slots: list[datetime]


class BookingRequest(BaseModel):
    session_slug: str = Field(min_length=1)
    package_id: int = Field(gt=0)
    start_at: datetime


class BookingResponse(BaseModel):
    session: str
    package: str
    price: Decimal
    start_at: datetime
    provider: str
    calendar_event_id: str | None = None
    message: str
    whatsapp_url: str


def _provider():
    if settings.calendar_provider == "google":
        return GoogleCalendarProvider()
    return MockAgendaProvider()


def _provider_name() -> str:
    return settings.calendar_provider


@router.get("/availability", response_model=AvailabilityResponse)
def availability(
    session_slug: str,
    package_id: int,
    target_date: date,
    db: Session = Depends(get_database),
):
    session = SessionRepository(db).get_active_by_slug(session_slug)
    if session is None:
        raise HTTPException(status_code=404, detail="Ensaio não encontrado.")

    package = next((item for item in session.packages if item.id == package_id and item.active), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")

    try:
        service = AgendaService(_provider())
        slots = service.available_slots(
            target_date=target_date,
            duration_minutes=package.duration_minutes,
        )
    except GoogleCalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível consultar o Google Calendar.") from exc

    return AvailabilityResponse(
        date=target_date,
        provider=_provider_name(),
        slots=[slot.start for slot in slots],
    )


@router.post("/whatsapp", response_model=BookingResponse)
def create_whatsapp_booking(
    request: BookingRequest,
    db: Session = Depends(get_database),
):
    session = SessionRepository(db).get_active_by_slug(request.session_slug)
    if session is None:
        raise HTTPException(status_code=404, detail="Ensaio não encontrado.")

    package = next(
        (item for item in session.packages if item.id == request.package_id and item.active),
        None,
    )
    if package is None:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")

    provider = _provider()
    try:
        slots = provider.list_available_slots(
            date=request.start_at.date(),
            duration_minutes=package.duration_minutes,
        )
    except GoogleCalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível validar a disponibilidade.") from exc

    if request.start_at not in {slot.start for slot in slots}:
        raise HTTPException(status_code=409, detail="Esse horário não está disponível.")

    event_id = None
    if settings.calendar_provider == "google":
        try:
            event_id = provider.create_booking(
                start_at=request.start_at,
                duration_minutes=package.duration_minutes,
                title=f"{session.name} - {package.name}",
                description=(
                    f"Ensaio: {session.name}\n"
                    f"Pacote: {package.name}\n"
                    f"Valor: R$ {package.price:.2f}"
                ),
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Não foi possível criar o evento no Google Calendar.") from exc

    whatsapp = WhatsAppService(settings.whatsapp_phone)
    message = whatsapp.build_booking_message(
        session_name=session.name,
        package_name=package.name,
        price=package.price,
        start_at=request.start_at,
    )

    return BookingResponse(
        session=session.name,
        package=package.name,
        price=package.price,
        start_at=request.start_at,
        provider=_provider_name(),
        calendar_event_id=event_id,
        message=message,
        whatsapp_url=whatsapp.build_url(message),
    )
