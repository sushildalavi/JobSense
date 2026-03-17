"""
Application and ApplicationEvent ORM models.
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
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.base import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.calendar import CalendarEvent
    from app.models.email import EmailThread
    from app.models.job import Job
    from app.models.resume import ResumeVersion
    from app.models.user import User


class ApplicationStatus(str, enum.Enum):
    discovered = "discovered"
    shortlisted = "shortlisted"
    tailored = "tailored"
    ready_to_apply = "ready_to_apply"
    applied = "applied"
    oa_received = "oa_received"
    recruiter_contacted = "recruiter_contacted"
    interview_scheduled = "interview_scheduled"
    rejected = "rejected"
    offer = "offer"
    archived = "archived"


class TriggeredBy(str, enum.Enum):
    user = "user"
    email_parser = "email_parser"
    agent = "agent"
    automation = "automation"


class Application(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Tracks a user's job application through its full lifecycle."""

    __tablename__ = "applications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status_enum"),
        default=ApplicationStatus.discovered,
        nullable=False,
        index=True,
    )
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_answers: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cover_letter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    application_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_of_discovery: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="applications")
    job: Mapped[Job] = relationship("Job", back_populates="applications")
    resume_version: Mapped[Optional[ResumeVersion]] = relationship("ResumeVersion")
    events: Mapped[list[ApplicationEvent]] = relationship(
        "ApplicationEvent", back_populates="application", order_by="ApplicationEvent.created_at"
    )
    email_threads: Mapped[list[EmailThread]] = relationship(
        "EmailThread", back_populates="application"
    )
    calendar_events: Mapped[list[CalendarEvent]] = relationship(
        "CalendarEvent", back_populates="application"
    )

    def __repr__(self) -> str:
        return f"<Application id={self.id} status={self.status!r}>"


class ApplicationEvent(Base):
    """Immutable record of every status transition for an application."""

    __tablename__ = "application_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    from_status: Mapped[Optional[str]] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status_enum", create_type=False),
        nullable=True,
    )
    to_status: Mapped[str] = mapped_column(
        SAEnum(ApplicationStatus, name="application_status_enum", create_type=False),
        nullable=False,
    )
    triggered_by: Mapped[str] = mapped_column(
        SAEnum(TriggeredBy, name="triggered_by_enum"),
        nullable=False,
        default=TriggeredBy.user,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    application: Mapped[Application] = relationship("Application", back_populates="events")

    def __repr__(self) -> str:
        return f"<ApplicationEvent {self.from_status} → {self.to_status}>"
