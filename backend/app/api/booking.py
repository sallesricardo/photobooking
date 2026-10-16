from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_database
from app.domain.agenda import MockAgendaProvider
from app.repositories.session import SessionRepository
from app.services.agenda import AgendaService
from app.services.whatsapp import WhatsAppService

router = APIRouter(prefix="/booking", tags=["booking"])

# Número fictício para desenvolvimento. Substituir por configuração do cliente.
WHATSAPP_PHONE = "5511999999999"


class AvailabilityResponse(BaseModel):
    date: date
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
    message: str
    whatsapp_url: str


@router.get("/")
def root():
    return {"name": "PhotoBooking API", "version": "v1"}


@router.get("/availability", response_model=AvailabilityResponse)
def availability(
    session_slug: str,
    package_id: int,
    target_date: date,
    db: Session = Depends(get_database),
):
    print("Get availability", session_slug, package_id, target_date)
    session = SessionRepository(db).get_active_by_slug(session_slug)
    if session is None:
        raise HTTPException(status_code=404, detail="Ensaio não encontrado.")

    package = next((item for item in session.packages if item.id == package_id and item.active), None)
    if package is None:
        raise HTTPException(status_code=404, detail="Pacote não encontrado.")

    service = AgendaService(MockAgendaProvider())
    slots = service.available_slots(
        target_date=target_date,
        duration_minutes=package.duration_minutes,
    )
    return AvailabilityResponse(
        date=target_date,
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

    service = AgendaService(MockAgendaProvider())
    slots = service.available_slots(
        target_date=request.start_at.date(),
        duration_minutes=package.duration_minutes,
    )
    if request.start_at not in {slot.start for slot in slots}:
        raise HTTPException(status_code=409, detail="Esse horário não está disponível.")

    whatsapp = WhatsAppService(WHATSAPP_PHONE)
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
        message=message,
        whatsapp_url=whatsapp.build_url(message),
    )
