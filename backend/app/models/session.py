from sqlalchemy import Boolean,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship
from app.db.session import Base


class PhotographySession(Base):
    __tablename__ = "photography_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text())
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    packages: Mapped[list["SessionPackage"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="SessionPackage.display_order")
