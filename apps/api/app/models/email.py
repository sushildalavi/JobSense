"""
Email intelligence ORM models: EmailThread, ParsedEmail.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.user import User


class EmailClassification(str, enum.Enum):
    recruiter_outreach = "recruiter_outreach"
    oa_assessment = "oa_assessment"
    interview_scheduling = "interview_scheduling"
    interview_confirmation = "interview_confirmation"
    rejection = "rejection"
    offer = "offer"
    follow_up = "follow_up"
    noise = "noise"
    unclassified = "unclassified"


class EmailThread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Represents a Gmail conversation thread related to a job application."""

    __tablename__ = "email_threads"

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

    # Gmail identifiers
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    participants: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    message_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    classification: Mapped[str] = mapped_column(
        SAEnum(EmailClassification, name="email_classification_enum"),
        default=EmailClassification.unclassified,
        nullable=False,
        index=True,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User")
    application: Mapped[Optional[Application]] = relationship(
        "Application", back_populates="email_threads"
    )
    parsed_emails: Mapped[list[ParsedEmail]] = relationship("ParsedEmail", back_populates="thread")

    def __repr__(self) -> str:
        return f"<EmailThread thread_id={self.thread_id!r} class={self.classification!r}>"


class ParsedEmail(Base):
    """
    A single parsed and entity-extracted email message.

    Stores both the raw and cleaned body plus all structured data
    extracted by the AI (interview time, meeting link, etc.).
    """

    __tablename__ = "parsed_emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("email_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Gmail message identifier
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    subject: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sender_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    raw_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cleaned_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification result
    classification: Mapped[str] = mapped_column(
        SAEnum(EmailClassification, name="email_classification_enum", create_type=False),
        default=EmailClassification.unclassified,
        nullable=False,
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Extracted entities
    extracted_company: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_job_title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    extracted_interviewer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_interview_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extracted_timezone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extracted_meeting_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_next_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Audit
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    thread: Mapped[EmailThread] = relationship("EmailThread", back_populates="parsed_emails")

    def __repr__(self) -> str:
        return f"<ParsedEmail message_id={self.message_id!r}>"
