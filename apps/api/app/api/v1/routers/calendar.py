"""
Calendar event endpoints.
"""

from __future__ import annotations

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_active_user,
    get_db,
    get_pagination,
)
from app.models.calendar import CalendarEvent
from app.models.user import User
from app.schemas.calendar import CalendarEventCreate, CalendarEventResponse, CalendarEventUpdate

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events", response_model=List[CalendarEventResponse])
async def list_events(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> List[CalendarEventResponse]:
    """List calendar events for the current user."""
    result = await db.execute(
        select(CalendarEvent)
        .where(CalendarEvent.user_id == current_user.id)
        .order_by(CalendarEvent.start_datetime.asc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    events = result.scalars().all()
    return [CalendarEventResponse.model_validate(e) for e in events]


@router.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    data: CalendarEventCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    """Create a new calendar event."""
    event = CalendarEvent(
        user_id=current_user.id,
        application_id=data.application_id,
        title=data.title,
        description=data.description,
        start_datetime=data.start_datetime,
        end_datetime=data.end_datetime,
        timezone=data.timezone,
        meeting_link=data.meeting_link,
        location=data.location,
        reminder_minutes=data.reminder_minutes,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    logger.info("Calendar event created", event_id=str(event.id))
    return CalendarEventResponse.model_validate(event)


@router.patch("/events/{event_id}", response_model=CalendarEventResponse)
async def update_event(
    event_id: uuid.UUID,
    data: CalendarEventUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CalendarEventResponse:
    """Update a calendar event."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return CalendarEventResponse.model_validate(event)


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a calendar event."""
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    await db.delete(event)
    await db.commit()
    logger.info("Calendar event deleted", event_id=str(event_id))


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_calendar(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger Google Calendar sync for the current user."""
    from app.tasks.calendar_tasks import sync_google_calendar

    sync_google_calendar.delay(str(current_user.id))
    return {"message": "Calendar sync triggered"}
