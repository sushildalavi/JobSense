"""
Calendar Celery tasks.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.tasks.calendar_tasks.create_interview_event",
    queue="calendar",
    max_retries=3,
    default_retry_delay=30,
)
def create_interview_event(self, parsed_email_id: str, user_id: str) -> Dict[str, Any]:
    """Create a calendar event from a parsed interview email."""
    logger.info("create_interview_event started", parsed_email_id=parsed_email_id)
    try:
        return _run_async(_create_interview_event_async(parsed_email_id, user_id))
    except Exception as exc:
        logger.error("create_interview_event failed", error=str(exc))
        raise self.retry(exc=exc)


async def _create_interview_event_async(
    parsed_email_id: str, user_id: str
) -> Dict[str, Any]:
    from app.core.database import AsyncSessionLocal
    from app.models.email import ParsedEmail
    from app.models.calendar import CalendarEvent, CalendarEventStatus
    from app.integrations.google_calendar.client import GoogleCalendarClient
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ParsedEmail).where(ParsedEmail.id == uuid.UUID(parsed_email_id))
        )
        parsed = result.scalar_one_or_none()
        if parsed is None or parsed.extracted_interview_datetime is None:
            return {"skipped": True, "reason": "no interview datetime"}

        from datetime import timedelta

        start_dt = parsed.extracted_interview_datetime
        end_dt = start_dt + timedelta(hours=1)
        title = f"Interview — {parsed.extracted_company or 'Unknown Company'}"
        if parsed.extracted_job_title:
            title += f" ({parsed.extracted_job_title})"

        # Check for existing event for this email
        existing = await db.execute(
            select(CalendarEvent).where(
                CalendarEvent.parsed_email_id == parsed.id
            )
        )
        if existing.scalar_one_or_none() is not None:
            return {"skipped": True, "reason": "event already exists"}

        event = CalendarEvent(
            user_id=uuid.UUID(user_id),
            parsed_email_id=parsed.id,
            title=title,
            start_datetime=start_dt,
            end_datetime=end_dt,
            timezone=parsed.extracted_timezone or "UTC",
            meeting_link=parsed.extracted_meeting_link,
            status=CalendarEventStatus.pending,
        )
        db.add(event)
        await db.flush()

        # Try to push to Google Calendar
        from app.models.user import User
        user_result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = user_result.scalar_one_or_none()
        if user and user.google_tokens:
            try:
                cal_client = GoogleCalendarClient(user.google_tokens)
                google_event_id = await cal_client.create_event(
                    title=event.title,
                    start_datetime=start_dt,
                    end_datetime=end_dt,
                    timezone=event.timezone,
                    meeting_link=event.meeting_link,
                )
                event.google_event_id = google_event_id
                event.status = CalendarEventStatus.confirmed
            except Exception as exc:
                logger.warning("Google Calendar push failed", error=str(exc))

        await db.commit()
        return {"event_id": str(event.id), "title": title}


@celery_app.task(
    bind=True,
    name="app.tasks.calendar_tasks.sync_google_calendar",
    queue="calendar",
    max_retries=3,
    default_retry_delay=60,
)
def sync_google_calendar(self, user_id: str) -> Dict[str, Any]:
    """Sync events from Google Calendar for a user."""
    logger.info("sync_google_calendar started", user_id=user_id)
    try:
        return _run_async(_sync_calendar_async(user_id))
    except Exception as exc:
        logger.error("sync_google_calendar failed", error=str(exc))
        raise self.retry(exc=exc)


async def _sync_calendar_async(user_id: str) -> Dict[str, Any]:
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.calendar import CalendarEvent, CalendarEventStatus
    from app.integrations.google_calendar.client import GoogleCalendarClient
    from sqlalchemy import select
    from datetime import datetime, timezone

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None or not user.google_tokens:
            return {"skipped": True, "reason": "no google tokens"}

        cal_client = GoogleCalendarClient(user.google_tokens)
        events = await cal_client.list_upcoming_events(max_results=50)

        synced = 0
        for event_data in events:
            google_event_id = event_data.get("id")
            if not google_event_id:
                continue

            existing = await db.execute(
                select(CalendarEvent).where(
                    CalendarEvent.google_event_id == google_event_id
                )
            )
            existing_event = existing.scalar_one_or_none()

            start = event_data.get("start", {})
            end = event_data.get("end", {})
            start_dt = start.get("dateTime") or start.get("date")
            end_dt = end.get("dateTime") or end.get("date")

            if not start_dt or not end_dt:
                continue

            from dateutil import parser as date_parser
            try:
                start_datetime = date_parser.parse(start_dt)
                end_datetime = date_parser.parse(end_dt)
            except Exception:
                continue

            if existing_event is None:
                event = CalendarEvent(
                    user_id=uuid.UUID(user_id),
                    google_event_id=google_event_id,
                    title=event_data.get("summary", "Untitled"),
                    description=event_data.get("description"),
                    start_datetime=start_datetime,
                    end_datetime=end_datetime,
                    timezone=start.get("timeZone", "UTC"),
                    meeting_link=event_data.get("hangoutLink"),
                    status=CalendarEventStatus.confirmed,
                )
                db.add(event)
                synced += 1

        await db.commit()
    return {"synced": synced}
