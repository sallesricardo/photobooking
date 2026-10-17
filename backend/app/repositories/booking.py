from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking: Booking) -> Booking:
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get(self, booking_id: int) -> Booking | None:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.session), joinedload(Booking.package))
            .where(Booking.id == booking_id)
        )
        return self.db.scalars(stmt).first()

    def find_by_provider_event_id(self, event_id: str) -> Booking | None:
        return self.db.scalar(select(Booking).where(Booking.provider_event_id == event_id))

    def find_by_idempotency_key(self, key: str) -> Booking | None:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.session), joinedload(Booking.package))
            .where(Booking.idempotency_key == key)
        )
        return self.db.scalars(stmt).first()

    def list_recent(self, limit: int = 100) -> list[Booking]:
        stmt = (
            select(Booking)
            .options(joinedload(Booking.session), joinedload(Booking.package))
            .order_by(Booking.start_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())
