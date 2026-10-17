from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, URLSafeSerializer

from app.api.auth import get_admin_username
from app.core.config import settings
from app.integrations.google.calendar import GoogleCalendarNotConfigured, GoogleCalendarProvider

router = APIRouter(prefix="/google", tags=["google-calendar"])
serializer = URLSafeSerializer(settings.app_secret_key, salt="google-oauth")


@router.get("/status")
def google_status(_username: str = Depends(get_admin_username)):

    provider = GoogleCalendarProvider()
    return {"connected": provider.is_authenticated(), "calendar_id": settings.google_calendar_id}


@router.get("/authorize")
def google_authorize(_username: str = Depends(get_admin_username)):

    provider = GoogleCalendarProvider()
    state = serializer.dumps({"provider": "google-calendar"})
    try:
        return RedirectResponse(provider.authorization_url(state))
    except GoogleCalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/callback")
def google_callback(code: str = Query(...), state: str = Query(...)):
    try:
        serializer.loads(state)
    except BadSignature as exc:
        raise HTTPException(status_code=400, detail="OAuth state inválido.") from exc

    provider = GoogleCalendarProvider()
    try:
        provider.complete_authorization(state=state, code=code)
    except GoogleCalendarNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Não foi possível concluir a autorização do Google.") from exc

    return {"connected": True, "message": "Google Calendar conectado com sucesso."}
