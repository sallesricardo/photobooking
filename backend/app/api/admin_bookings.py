from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import get_admin_username
from app.api.dependencies import get_database
from app.repositories.booking import BookingRepository

router = APIRouter(prefix="/admin/bookings", tags=["admin-bookings"])


class AdminBookingResponse(BaseModel):
    id: int
    session: str
    package: str
    price: Decimal
    start_at: datetime
    end_at: datetime
    provider: str
    provider_event_id: str | None
    status: str
    customer_name: str | None
    customer_phone: str | None
    whatsapp_url: str
    created_at: datetime


@router.get("", response_model=list[AdminBookingResponse])
def list_bookings(
    _username: str = Depends(get_admin_username),
    db: Session = Depends(get_database),
):
    bookings = BookingRepository(db).list_recent()
    return [
        AdminBookingResponse(
            id=item.id,
            session=item.session.name,
            package=item.package.name,
            price=item.package.price,
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
        for item in bookings
    ]
