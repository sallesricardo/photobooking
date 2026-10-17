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


class GoogleCalendarUnavailable(RuntimeError):
    """Temporary Google API failure; the operation may succeed on retry."""


class GoogleCalendarOperationError(RuntimeError):
    """Non-retryable Google Calendar API failure."""


_TRANSIENT_HTTP_STATUSES = {429, 500, 502, 503, 504}


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

        response = self._execute_with_retry(
            lambda: service.freebusy()
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
        idempotency_key: str | None = None,
    ) -> str:
        service = self._service()
        start_at = self._normalize_datetime(start_at)
        end_at = start_at + timedelta(minutes=duration_minutes)

        # If a previous request created the external event but failed before
        # committing PostgreSQL, the same idempotency key lets a retry recover
        # the existing Google event instead of creating a duplicate.
        if idempotency_key:
            existing_id = self._find_event_by_idempotency_key(service, idempotency_key)
            if existing_id:
                return existing_id

        # Recheck immediately before insertion to reduce the chance of a race
        # between availability lookup and booking creation. This read is safe
        # to retry; the subsequent POST is intentionally not retried because it
        # is a non-idempotent external operation.
        response = self._execute_with_retry(
            lambda: service.freebusy()
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
        if idempotency_key:
            event["extendedProperties"] = {
                "private": {"photobooking_idempotency_key": idempotency_key}
            }

        try:
            created = service.events().insert(calendarId=self.calendar_id, body=event).execute()
        except HttpError as exc:
            self._raise_google_error(exc)
        return created["id"]

    def cancel_booking(self, *, provider_event_id: str) -> None:
        service = self._service()
        try:
            service.events().delete(
                calendarId=self.calendar_id,
                eventId=provider_event_id,
            ).execute()
        except HttpError as exc:
            if getattr(exc, "resp", None) is not None and exc.resp.status == 404:
                return
            self._raise_google_error(exc)

    def reschedule_booking(
        self,
        *,
        provider_event_id: str,
        new_start_at: datetime,
        duration_minutes: int,
    ) -> None:
        service = self._service()
        new_start_at = self._normalize_datetime(new_start_at)
        new_end_at = new_start_at + timedelta(minutes=duration_minutes)

        existing = service.events().get(
            calendarId=self.calendar_id,
            eventId=provider_event_id,
        ).execute()

        response = self._execute_with_retry(
            lambda: service.freebusy()
            .query(
                body={
                    "timeMin": new_start_at.isoformat(),
                    "timeMax": new_end_at.isoformat(),
                    "timeZone": settings.app_timezone,
                    "items": [{"id": self.calendar_id}],
                }
            )
            .execute()
        )

        busy = response.get("calendars", {}).get(self.calendar_id, {}).get("busy", [])
        current_start = existing.get("start", {}).get("dateTime")
        current_end = existing.get("end", {}).get("dateTime")
        current_interval = None
        if current_start and current_end:
            current_interval = (
                datetime.fromisoformat(current_start.replace("Z", "+00:00")),
                datetime.fromisoformat(current_end.replace("Z", "+00:00")),
            )

        for item in busy:
            busy_start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
            busy_end = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))
            if current_interval and busy_start == current_interval[0] and busy_end == current_interval[1]:
                continue
            raise ValueError("O novo horário escolhido está indisponível.")

        service.events().patch(
            calendarId=self.calendar_id,
            eventId=provider_event_id,
            body={
                "start": {"dateTime": new_start_at.isoformat(), "timeZone": settings.app_timezone},
                "end": {"dateTime": new_end_at.isoformat(), "timeZone": settings.app_timezone},
            },
        ).execute()

    def _find_event_by_idempotency_key(self, service: Resource, key: str) -> str | None:
        try:
            response = self._execute_with_retry(
                lambda: service.events()
                .list(
                    calendarId=self.calendar_id,
                    privateExtendedProperty=[f"photobooking_idempotency_key={key}"],
                    showDeleted=False,
                    maxResults=10,
                )
                .execute()
            )
        except GoogleCalendarUnavailable:
            raise

        for item in response.get("items", []):
            event_id = item.get("id")
            if event_id:
                return event_id
        return None

    def _execute_with_retry(self, operation, *, attempts: int = 3):
        import time

        for attempt in range(attempts):
            try:
                return operation()
            except HttpError as exc:
                status = getattr(getattr(exc, "resp", None), "status", None)
                if status not in _TRANSIENT_HTTP_STATUSES or attempt == attempts - 1:
                    self._raise_google_error(exc)
                time.sleep(0.2 * (2**attempt))

        raise AssertionError("unreachable")

    @staticmethod
    def _raise_google_error(exc: HttpError) -> None:
        status = getattr(getattr(exc, "resp", None), "status", None)
        if status in _TRANSIENT_HTTP_STATUSES:
            raise GoogleCalendarUnavailable(
                "O Google Calendar está temporariamente indisponível. Tente novamente."
            ) from exc
        raise GoogleCalendarOperationError(
            "O Google Calendar recusou a operação solicitada."
        ) from exc

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
