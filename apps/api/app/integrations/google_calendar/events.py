"""
Google Calendar event helpers — creation from parsed email data.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


def build_interview_event_body(
    title: str,
    start_datetime: datetime,
    end_datetime: Optional[datetime] = None,
    timezone: str = "UTC",
    description: Optional[str] = None,
    meeting_link: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    reminder_minutes: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Build a Google Calendar API event body dict.

    Args:
        title: Event summary/title
        start_datetime: Event start time (timezone-aware recommended)
        end_datetime: Event end time. Defaults to start + 1 hour.
        timezone: IANA timezone name
        description: Optional description or notes
        meeting_link: Zoom/Meet/Teams URL
        location: Physical or virtual location
        attendees: List of attendee email addresses
        reminder_minutes: List of reminder offsets in minutes before event

    Returns:
        Dict suitable for Google Calendar API insert/update
    """
    if end_datetime is None:
        end_datetime = start_datetime + timedelta(hours=1)

    body_description = description or ""
    if meeting_link:
        body_description = f"Meeting Link: {meeting_link}\n\n{body_description}".strip()

    event: Dict[str, Any] = {
        "summary": title,
        "description": body_description,
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
                for m in (reminder_minutes or [30, 60])
            ],
        },
    }

    if location:
        event["location"] = location

    if attendees:
        event["attendees"] = [{"email": e} for e in attendees]

    return event


def parse_google_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw Google Calendar event dict to our internal format.
    """
    start = raw_event.get("start", {})
    end = raw_event.get("end", {})

    start_dt_str = start.get("dateTime") or start.get("date")
    end_dt_str = end.get("dateTime") or end.get("date")

    from dateutil import parser as date_parser

    start_dt = date_parser.parse(start_dt_str) if start_dt_str else None
    end_dt = date_parser.parse(end_dt_str) if end_dt_str else None

    attendees = [
        a.get("email") for a in raw_event.get("attendees", []) if a.get("email")
    ]

    conference = raw_event.get("conferenceData") or {}
    entry_points = conference.get("entryPoints", [])
    meeting_link = next(
        (ep.get("uri") for ep in entry_points if ep.get("entryPointType") == "video"),
        raw_event.get("hangoutLink"),
    )

    return {
        "google_event_id": raw_event.get("id"),
        "title": raw_event.get("summary", "Untitled Event"),
        "description": raw_event.get("description"),
        "start_datetime": start_dt,
        "end_datetime": end_dt,
        "timezone": start.get("timeZone", "UTC"),
        "meeting_link": meeting_link,
        "location": raw_event.get("location"),
        "attendees": attendees,
        "status": raw_event.get("status", "confirmed"),
    }
