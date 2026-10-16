from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.models.session import PhotographySession


class SessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_active(self):
        return list(self.db.scalars(
            select(PhotographySession).where(PhotographySession.active.is_(True)).order_by(PhotographySession.id)).all()
        )

    def get_active_by_slug(self, slug: str):
        stmt = select(PhotographySession).where(PhotographySession.slug == slug, PhotographySession.active.is_(True)).options(selectinload(PhotographySession.packages))
        return self.db.scalars(stmt).first()
