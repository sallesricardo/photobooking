from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.core.config import settings
from app.domain.agenda import MockAgendaProvider
from app.integrations.google.calendar import (
    GoogleCalendarNotConfigured,
    GoogleCalendarOperationError,
    GoogleCalendarProvider,
    GoogleCalendarUnavailable,
)
from app.models.booking import Booking
from app.repositories.booking import BookingRepository
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
    id: int
    session: str
    package: str
    price: Decimal
    start_at: datetime
    end_at: datetime
    provider: str
    calendar_event_id: str | None = None
    status: str
    message: str
    whatsapp_url: str


def _provider():
    if settings.calendar_provider == "google":
        return GoogleCalendarProvider()
    return MockAgendaProvider()


def _provider_name() -> str:
    return settings.calendar_provider


def _build_response(booking: Booking) -> BookingResponse:
    message = WhatsAppService(settings.whatsapp_phone).build_booking_message(
        session_name=booking.session.name,
        package_name=booking.package.name,
        price=booking.package.price,
        start_at=booking.start_at,
    )
    return BookingResponse(
        id=booking.id,
        session=booking.session.name,
        package=booking.package.name,
        price=booking.package.price,
        start_at=booking.start_at,
        end_at=booking.end_at,
        provider=booking.provider,
        calendar_event_id=booking.provider_event_id,
        status=booking.status,
        message=message,
        whatsapp_url=booking.whatsapp_url,
    )


@router.get("/availability", response_model=AvailabilityResponse)
def availability(session_slug: str, package_id: int, target_date: date, db: Session = Depends(get_database)):
    session = SessionRepository(db).get_active_by_slug(session_slug)
    if session is None:
        raise HTTPException(status_code=404, detail="Ensaio não encontrado.")
    package = next((item for item in session.packages if item.id == package_id and item.active), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")
    try:
        slots = AgendaService(_provider()).available_slots(target_date=target_date, duration_minutes=package.duration_minutes)
    except GoogleCalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível consultar a agenda.") from exc
    return AvailabilityResponse(date=target_date, provider=_provider_name(), slots=[slot.start for slot in slots])


@router.post("/whatsapp", response_model=BookingResponse)
def create_whatsapp_booking(
    request: BookingRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_database),
):
    key = idempotency_key or str(uuid4())
    repository = BookingRepository(db)
    existing = repository.find_by_idempotency_key(key)
    if existing:
        return _build_response(existing)

    session = SessionRepository(db).get_active_by_slug(request.session_slug)
    if session is None:
        raise HTTPException(status_code=404, detail="Ensaio não encontrado.")
    package = next((item for item in session.packages if item.id == request.package_id and item.active), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")

    provider = _provider()
    try:
        slots = provider.list_available_slots(date=request.start_at.date(), duration_minutes=package.duration_minutes)
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
                description=f"Ensaio: {session.name}\nPacote: {package.name}\nValor: R$ {package.price:.2f}",
                idempotency_key=key,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except GoogleCalendarUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except GoogleCalendarOperationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Não foi possível criar o evento no Google Calendar.") from exc

    whatsapp = WhatsAppService(settings.whatsapp_phone)
    message = whatsapp.build_booking_message(session_name=session.name, package_name=package.name, price=package.price, start_at=request.start_at)
    booking = Booking(
        session_id=session.id, package_id=package.id, start_at=request.start_at,
        end_at=request.start_at + timedelta(minutes=package.duration_minutes),
        provider=_provider_name(), provider_event_id=event_id, status="confirmed",
        idempotency_key=key, whatsapp_url=whatsapp.build_url(message),
    )
    try:
        created = repository.create(booking)
    except IntegrityError:
        db.rollback()
        duplicate = repository.find_by_idempotency_key(key)
        if duplicate:
            if event_id and duplicate.provider_event_id != event_id and settings.calendar_provider == "google":
                try:
                    provider.cancel_booking(provider_event_id=event_id)
                except Exception:
                    pass
            return _build_response(duplicate)
        if event_id and settings.calendar_provider == "google":
            try:
                provider.cancel_booking(provider_event_id=event_id)
            except Exception:
                pass
        raise HTTPException(status_code=409, detail="Não foi possível registrar a reserva.")
    except Exception:
        db.rollback()
        if event_id and settings.calendar_provider == "google":
            try:
                provider.cancel_booking(provider_event_id=event_id)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail="Não foi possível registrar a reserva.")
    return _build_response(created)
