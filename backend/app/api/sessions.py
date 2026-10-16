from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_database
from app.repositories.session import SessionRepository
from app.schemas.session import SessionDetailResponse, SessionListResponse

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionListResponse])
def list_sessions(db: Session = Depends(get_database)):
    return SessionRepository(db).list_active()


@router.get("/{slug}", response_model=SessionDetailResponse)
def get_session(slug: str, db: Session = Depends(get_database)):
    session = SessionRepository(db).get_active_by_slug(slug)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ensaio não encontrado.")
    return session
