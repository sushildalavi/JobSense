"""
Google Calendar API client.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = structlog.get_logger(__name__)


class GoogleCalendarClient:
    """Wrapper around the Google Calendar API."""

    def __init__(self, token_dict: Dict[str, Any]) -> None:
        self._credentials = Credentials(
            token=token_dict.get("token"),
            refresh_token=token_dict.get("refresh_token"),
            token_uri=token_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=None,
            client_secret=None,
        )
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = build("calendar", "v3", credentials=self._credentials)
        return self._service

    async def create_event(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        timezone: str = "UTC",
        description: Optional[str] = None,
        meeting_link: Optional[str] = None,
        location: Optional[str] = None,
        reminder_minutes: Optional[List[int]] = None,
        calendar_id: str = "primary",
    ) -> Optional[str]:
        """
        Create a Google Calendar event.

        Returns the Google event ID on success, or None on failure.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._create_event_sync,
            title,
            start_datetime,
            end_datetime,
            timezone,
            description,
            meeting_link,
            location,
            reminder_minutes or [30, 60],
            calendar_id,
        )

    def _create_event_sync(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        timezone: str,
        description: Optional[str],
        meeting_link: Optional[str],
        location: Optional[str],
        reminder_minutes: List[int],
        calendar_id: str,
    ) -> Optional[str]:
        service = self._get_service()

        body_description = description or ""
        if meeting_link:
            body_description += f"\n\nMeeting Link: {meeting_link}"

        event_body: Dict[str, Any] = {
            "summary": title,
            "description": body_description.strip(),
            "start": {
                "dateTime": start_datetime.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_datetime.isoformat(),
                "timeZone": timezone,
            },
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": m}
                    for m in reminder_minutes
                ],
            },
        }
        if location:
            event_body["location"] = location

        try:
            event = (
                service.events()
                .insert(calendarId=calendar_id, body=event_body)
                .execute()
            )
            logger.info("Google Calendar event created", event_id=event.get("id"))
            return event.get("id")
        except HttpError as exc:
            logger.error("Google Calendar create_event failed", error=str(exc))
            return None

    async def update_event(
        self,
        google_event_id: str,
        updates: Dict[str, Any],
        calendar_id: str = "primary",
    ) -> bool:
        """Update a Google Calendar event. Returns True on success."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._update_event_sync, google_event_id, updates, calendar_id
        )

    def _update_event_sync(
        self,
        google_event_id: str,
        updates: Dict[str, Any],
        calendar_id: str,
    ) -> bool:
        service = self._get_service()
        try:
            # Fetch existing event
            event = (
                service.events()
                .get(calendarId=calendar_id, eventId=google_event_id)
                .execute()
            )
            event.update(updates)
            service.events().update(
                calendarId=calendar_id, eventId=google_event_id, body=event
            ).execute()
            return True
        except HttpError as exc:
            logger.error("Google Calendar update_event failed", error=str(exc))
            return False

    async def delete_event(
        self, google_event_id: str, calendar_id: str = "primary"
    ) -> bool:
        """Delete a Google Calendar event. Returns True on success."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._delete_event_sync, google_event_id, calendar_id
        )

    def _delete_event_sync(self, google_event_id: str, calendar_id: str) -> bool:
        service = self._get_service()
        try:
            service.events().delete(
                calendarId=calendar_id, eventId=google_event_id
            ).execute()
            return True
        except HttpError as exc:
            logger.error("Google Calendar delete_event failed", error=str(exc))
            return False

    async def list_upcoming_events(
        self,
        max_results: int = 50,
        calendar_id: str = "primary",
    ) -> List[Dict[str, Any]]:
        """List upcoming calendar events starting from now."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._list_events_sync, max_results, calendar_id
        )

    def _list_events_sync(
        self, max_results: int, calendar_id: str
    ) -> List[Dict[str, Any]]:
        service = self._get_service()
        from datetime import timezone
        now = datetime.now(timezone.utc).isoformat()
        try:
            result = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            return result.get("items", [])
        except HttpError as exc:
            logger.error("Google Calendar list_events failed", error=str(exc))
            return []
