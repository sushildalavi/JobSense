"""
Agent and automation session ORM models.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class WorkflowName(str, enum.Enum):
    job_discovery = "job_discovery"
    job_matching = "job_matching"
    resume_tailoring = "resume_tailoring"
    email_classification = "email_classification"
    email_extraction = "email_extraction"
    calendar_automation = "calendar_automation"
    follow_up_draft = "follow_up_draft"


class AgentRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class SessionType(str, enum.Enum):
    form_fill = "form_fill"
    resume_upload = "resume_upload"
    survey = "survey"
    other = "other"


class SessionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class AgentRun(Base):
    """
    Records every LangGraph workflow execution for auditability and debugging.
    """

    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    workflow_name: Mapped[str] = mapped_column(
        SAEnum(WorkflowName, name="workflow_name_enum"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(AgentRunStatus, name="agent_run_status_enum"),
        default=AgentRunStatus.pending,
        nullable=False,
        index=True,
    )

    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} workflow={self.workflow_name!r} status={self.status!r}>"


class AutomationSession(Base):
    """
    Records an autonomous browser automation session (e.g. form fill, resume upload).
    """

    __tablename__ = "automation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
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

    session_type: Mapped[str] = mapped_column(
        SAEnum(SessionType, name="session_type_enum"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        SAEnum(SessionStatus, name="session_status_enum"),
        default=SessionStatus.pending,
        nullable=False,
        index=True,
    )

    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    screenshot_urls: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    action_log: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    def __repr__(self) -> str:
        return f"<AutomationSession id={self.id} type={self.session_type!r} status={self.status!r}>"
