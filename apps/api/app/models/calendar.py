"""
CalendarEvent ORM model.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.email import ParsedEmail
    from app.models.user import User


class CalendarEventStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class CalendarEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A calendar event (typically an interview) synced with Google Calendar."""

    __tablename__ = "calendar_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parsed_email_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parsed_emails.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Google Calendar reference
    google_event_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="UTC")
    meeting_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(CalendarEventStatus, name="calendar_event_status_enum"),
        default=CalendarEventStatus.pending,
        nullable=False,
        index=True,
    )

    # List of reminder offsets in minutes, e.g. [30, 60]
    reminder_minutes: Mapped[Optional[list]] = mapped_column(JSON, default=lambda: [30, 60])

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User")
    application: Mapped[Optional[Application]] = relationship(
        "Application", back_populates="calendar_events"
    )
    parsed_email: Mapped[Optional[ParsedEmail]] = relationship("ParsedEmail")

    def __repr__(self) -> str:
        return f"<CalendarEvent id={self.id} title={self.title!r} start={self.start_datetime}>"
