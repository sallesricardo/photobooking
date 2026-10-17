from datetime import datetime, timedelta, timezone
from hmac import compare_digest

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

serializer = URLSafeTimedSerializer(settings.app_secret_key, salt="admin-session")
SESSION_COOKIE = "photobooking_admin"


class LoginRequest(BaseModel):
    username: str
    password: str


def _create_session(username: str) -> str:
    return serializer.dumps({"username": username, "role": "admin"})


def get_admin_username(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Autenticação necessária.")

    try:
        data = serializer.loads(token, max_age=settings.admin_session_minutes * 60)
    except BadSignature as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida ou expirada.") from exc

    if data.get("role") != "admin" or not data.get("username"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    return str(data["username"])


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    if not compare_digest(payload.username, settings.admin_username) or not compare_digest(
        payload.password, settings.admin_password
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")

    response.set_cookie(
        SESSION_COOKIE,
        _create_session(payload.username),
        httponly=True,
        samesite="lax",
        secure=settings.admin_cookie_secure,
        max_age=settings.admin_session_minutes * 60,
        path="/",
    )
    return {"authenticated": True, "username": payload.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"authenticated": False}


@router.get("/me")
def me(request: Request):
    username = get_admin_username(request)
    return {"authenticated": True, "username": username, "expires_in_minutes": settings.admin_session_minutes}
