from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_start_at", "start_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("photography_sessions.id", ondelete="RESTRICT"), index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("session_packages.id", ondelete="RESTRICT"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_event_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="confirmed")
    customer_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    customer_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    whatsapp_url: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    session: Mapped["PhotographySession"] = relationship()
    package: Mapped["SessionPackage"] = relationship()
