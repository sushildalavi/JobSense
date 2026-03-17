"""
User Profile ORM model.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User

import enum


class RemotePreference(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    flexible = "flexible"


class SeniorityLevel(str, enum.Enum):
    intern = "intern"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff = "staff"
    principal = "principal"
    director = "director"
    vp = "vp"
    c_level = "c_level"


class Profile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Extended user profile capturing job-search preferences."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # ── Job preferences ───────────────────────────────────────────────────────
    target_roles: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    remote_preference: Mapped[Optional[str]] = mapped_column(
        SAEnum(RemotePreference, name="remote_preference_enum"), nullable=True
    )
    seniority_level: Mapped[Optional[str]] = mapped_column(
        SAEnum(SeniorityLevel, name="seniority_level_enum"), nullable=True
    )
    preferred_industries: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Visa / authorization ──────────────────────────────────────────────────
    visa_status: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    work_authorization: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Salary ────────────────────────────────────────────────────────────────
    preferred_salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferred_salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    preferred_currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)

    # ── Skills & keywords ─────────────────────────────────────────────────────
    skills: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    keywords_to_prioritize: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    keywords_to_avoid: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # ── Online presence ───────────────────────────────────────────────────────
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    github_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    portfolio_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        return f"<Profile id={self.id} user_id={self.user_id}>"
