from __future__ import annotations

from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import HttpRequest

from app.core.config import settings
from app.domain.agenda import AvailabilitySlot


class GoogleCalendarNotConfigured(RuntimeError):
    pass


class GoogleCalendarProvider:
    """Google Calendar adapter used by the application service layer."""

    def __init__(self) -> None:
        self.calendar_id = settings.google_calendar_id
        self.timezone = ZoneInfo(settings.app_timezone)

    @property
    def scopes(self) -> list[str]:
        return [
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/calendar.freebusy",
        ]

    def is_authenticated(self) -> bool:
        return self._credentials() is not None

    def authorization_url(self, state: str) -> str:
        flow = self._flow(state=state)
        url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return url

    def complete_authorization(self, *, state: str, code: str) -> None:
        flow = self._flow(state=state)
        flow.fetch_token(code=code)
        credentials = flow.credentials
        self._save_credentials(credentials)

    def list_available_slots(
        self,
        *,
        target_date: date,
        duration_minutes: int,
        opening_hour: int = 9,
        closing_hour: int = 18,
        slot_interval_minutes: int = 30,
    ) -> list[AvailabilitySlot]:
        service = self._service()
        opening = datetime.combine(target_date, time(opening_hour), self.timezone)
        closing = datetime.combine(target_date, time(closing_hour), self.timezone)
        duration = timedelta(minutes=duration_minutes)
        step = timedelta(minutes=slot_interval_minutes)

        response = (
            service.freebusy()
            .query(
                body={
                    "timeMin": opening.isoformat(),
                    "timeMax": closing.isoformat(),
                    "timeZone": settings.app_timezone,
                    "items": [{"id": self.calendar_id}],
                }
            )
            .execute()
        )

        busy = [
            (
                datetime.fromisoformat(item["start"].replace("Z", "+00:00")),
                datetime.fromisoformat(item["end"].replace("Z", "+00:00")),
            )
            for item in response.get("calendars", {})
            .get(self.calendar_id, {})
            .get("busy", [])
        ]

        slots: list[AvailabilitySlot] = []
        current = opening
        while current + duration <= closing:
            end = current + duration
            if not any(current < busy_end and end > busy_start for busy_start, busy_end in busy):
                slots.append(AvailabilitySlot(start=current, end=end))
            current += step

        return slots

    def create_booking(
        self,
        *,
        start_at: datetime,
        duration_minutes: int,
        title: str,
        description: str,
    ) -> str:
        service = self._service()
        start_at = self._normalize_datetime(start_at)
        end_at = start_at + timedelta(minutes=duration_minutes)

        # Recheck immediately before insertion to reduce the chance of a race
        # between availability lookup and booking creation.
        response = (
            service.freebusy()
            .query(
                body={
                    "timeMin": start_at.isoformat(),
                    "timeMax": end_at.isoformat(),
                    "timeZone": settings.app_timezone,
                    "items": [{"id": self.calendar_id}],
                }
            )
            .execute()
        )
        busy = response.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        if busy:
            raise ValueError("O horário escolhido acabou de ficar indisponível.")

        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_at.isoformat(), "timeZone": settings.app_timezone},
            "end": {"dateTime": end_at.isoformat(), "timeZone": settings.app_timezone},
        }
        created = service.events().insert(calendarId=self.calendar_id, body=event).execute()
        return created["id"]

    def _credentials(self) -> Credentials | None:
        token_path = Path(settings.google_token_path)
        if not token_path.exists():
            return None

        credentials = Credentials.from_authorized_user_file(str(token_path), self.scopes)
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            self._save_credentials(credentials)
        return credentials if credentials.valid else None

    def _service(self) -> Resource:
        credentials = self._credentials()
        if credentials is None:
            raise GoogleCalendarNotConfigured("Google Calendar não está conectado.")
        return build("calendar", "v3", credentials=credentials, cache_discovery=False)

    def _flow(self, *, state: str) -> Flow:
        if not settings.google_client_id or not settings.google_client_secret:
            raise GoogleCalendarNotConfigured("Configure GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET.")

        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri],
            }
        }
        return Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            state=state,
            redirect_uri=settings.google_redirect_uri,
        )

    def _save_credentials(self, credentials: Credentials) -> None:
        token_path = Path(settings.google_token_path)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(credentials.to_json(), encoding="utf-8")

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=self.timezone)
        return value.astimezone(self.timezone)
