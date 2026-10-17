from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_admin_username
from app.api.dependencies import get_database
from app.core.config import settings
from app.domain.agenda import MockAgendaProvider
from app.integrations.google.calendar import (
    GoogleCalendarNotConfigured,
    GoogleCalendarOperationError,
    GoogleCalendarProvider,
    GoogleCalendarUnavailable,
)
from app.repositories.booking import BookingRepository

router = APIRouter(prefix="/admin/bookings", tags=["admin-bookings"])


class AdminBookingResponse(BaseModel):
    id: int
    session: str
    package: str
    price: str
    start_at: datetime
    end_at: datetime
    provider: str
    provider_event_id: str | None
    status: str
    customer_name: str | None
    customer_phone: str | None
    whatsapp_url: str
    created_at: datetime


class RescheduleRequest(BaseModel):
    start_at: datetime


def _provider():
    return GoogleCalendarProvider() if settings.calendar_provider == "google" else MockAgendaProvider()


def _serialize(item):
    return AdminBookingResponse(
        id=item.id,
        session=item.session.name,
        package=item.package.name,
        price=str(item.package.price),
        start_at=item.start_at,
        end_at=item.end_at,
        provider=item.provider,
        provider_event_id=item.provider_event_id,
        status=item.status,
        customer_name=item.customer_name,
        customer_phone=item.customer_phone,
        whatsapp_url=item.whatsapp_url,
        created_at=item.created_at,
    )


@router.get("", response_model=list[AdminBookingResponse])
def list_bookings(_username: str = Depends(get_admin_username), db: Session = Depends(get_database)):
    return [_serialize(item) for item in BookingRepository(db).list_recent()]


@router.post("/{booking_id}/cancel", response_model=AdminBookingResponse)
def cancel_booking(booking_id: int, _username: str = Depends(get_admin_username), db: Session = Depends(get_database)):
    repository = BookingRepository(db)
    booking = repository.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    if booking.status == "canceled":
        return _serialize(booking)
    if booking.status != "confirmed":
        raise HTTPException(status_code=409, detail="A reserva não pode ser cancelada neste estado.")

    if booking.provider_event_id:
        try:
            _provider().cancel_booking(provider_event_id=booking.provider_event_id)
        except GoogleCalendarNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except GoogleCalendarUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except GoogleCalendarOperationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Não foi possível cancelar o evento na agenda.") from exc

    booking.status = "canceled"
    db.commit()
    db.refresh(booking)
    return _serialize(booking)


@router.post("/{booking_id}/reschedule", response_model=AdminBookingResponse)
def reschedule_booking(
    booking_id: int,
    request: RescheduleRequest,
    _username: str = Depends(get_admin_username),
    db: Session = Depends(get_database),
):
    repository = BookingRepository(db)
    booking = repository.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Reserva não encontrada.")
    if booking.status != "confirmed":
        raise HTTPException(status_code=409, detail="Somente reservas confirmadas podem ser reagendadas.")
    if request.start_at == booking.start_at:
        return _serialize(booking)

    provider = _provider()
    try:
        slots = provider.list_available_slots(
            date=request.start_at.date(),
            duration_minutes=booking.package.duration_minutes,
        )
    except GoogleCalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Não foi possível consultar a disponibilidade.") from exc

    if request.start_at not in {slot.start for slot in slots}:
        raise HTTPException(status_code=409, detail="O novo horário não está disponível.")

    if booking.provider_event_id:
        try:
            provider.reschedule_booking(
                provider_event_id=booking.provider_event_id,
                new_start_at=request.start_at,
                duration_minutes=booking.package.duration_minutes,
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except GoogleCalendarNotConfigured as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except GoogleCalendarUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except GoogleCalendarOperationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail="Não foi possível reagendar o evento na agenda.") from exc

    from datetime import timedelta
    booking.start_at = request.start_at
    booking.end_at = request.start_at + timedelta(minutes=booking.package.duration_minutes)
    db.commit()
    db.refresh(booking)
    return _serialize(booking)
