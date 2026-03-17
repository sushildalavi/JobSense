"""
Calendar event Pydantic v2 schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, model_config, field_validator

from app.models.calendar import CalendarEventStatus


class CalendarEventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=512)
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = Field(default="UTC", max_length=100)
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    application_id: Optional[uuid.UUID] = None
    reminder_minutes: Optional[List[int]] = Field(default_factory=lambda: [30, 60])

    @field_validator("end_datetime")
    @classmethod
    def end_after_start(cls, v: datetime, info) -> datetime:
        if info.data.get("start_datetime") and v <= info.data["start_datetime"]:
            raise ValueError("end_datetime must be after start_datetime")
        return v


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=512)
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    timezone: Optional[str] = Field(default=None, max_length=100)
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    status: Optional[CalendarEventStatus] = None
    reminder_minutes: Optional[List[int]] = None


class CalendarEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    parsed_email_id: Optional[uuid.UUID] = None
    google_event_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: str
    meeting_link: Optional[str] = None
    location: Optional[str] = None
    status: CalendarEventStatus
    reminder_minutes: Optional[List[int]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
