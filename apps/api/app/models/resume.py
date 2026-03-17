"""
Resume ORM models: MasterResume and ResumeVersion.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.application import Application
    from app.models.job import Job


class MasterResume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    A user's canonical, unmodified resume that acts as the
    source of truth for all tailored versions.
    """

    __tablename__ = "master_resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="master_resumes")
    versions: Mapped[list[ResumeVersion]] = relationship(
        "ResumeVersion", back_populates="master_resume", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<MasterResume id={self.id} name={self.name!r}>"


class ResumeVersion(Base):
    """
    A tailored resume derived from a MasterResume for a specific job.

    Tracks what was changed and why, including the AI model and prompt
    version used so tailoring decisions are auditable.
    """

    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    master_resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("master_resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    application_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tailored_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tailored_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tailoring_strategy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    master_resume: Mapped[MasterResume] = relationship(
        "MasterResume", back_populates="versions"
    )

    def __repr__(self) -> str:
        return f"<ResumeVersion id={self.id} name={self.name!r}>"
