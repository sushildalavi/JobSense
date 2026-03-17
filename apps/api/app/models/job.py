"""
Job-related ORM models:
- JobSource
- Job
- JobDedupCluster
- JobClusterMember
- JobMatch
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.application import Application
    from app.models.user import User


# ── Enums ─────────────────────────────────────────────────────────────────────


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    internship = "internship"
    freelance = "freelance"


class JobSeniority(str, enum.Enum):
    intern = "intern"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff = "staff"
    principal = "principal"
    director = "director"
    vp = "vp"
    c_level = "c_level"


class JobStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    removed = "removed"


# ── JobSource ─────────────────────────────────────────────────────────────────


class JobSource(Base):
    """Represents an external data source from which jobs are ingested."""

    __tablename__ = "job_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    connector_type: Mapped[str] = mapped_column(String(100), nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    jobs: Mapped[list[Job]] = relationship("Job", back_populates="source")

    def __repr__(self) -> str:
        return f"<JobSource name={self.name!r}>"


# ── Job ───────────────────────────────────────────────────────────────────────


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A normalised job posting from any source."""

    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source_id", "source_job_id", name="uq_job_source_job_id"),)

    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_job_id: Mapped[str] = mapped_column(String(512), nullable=False, index=True)

    # ── Company ───────────────────────────────────────────────────────────────
    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    company_website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Posting details ───────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_hybrid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_onsite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    employment_type: Mapped[Optional[str]] = mapped_column(
        SAEnum(EmploymentType, name="employment_type_enum"), nullable=True
    )
    seniority: Mapped[Optional[str]] = mapped_column(
        SAEnum(JobSeniority, name="job_seniority_enum"), nullable=True
    )

    # ── Salary ────────────────────────────────────────────────────────────────
    salary_text: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    salary_min: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # ── Description ───────────────────────────────────────────────────────────
    raw_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cleaned_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    preferred_qualifications: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    responsibilities: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    # ── URLs / metadata ───────────────────────────────────────────────────────
    apply_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    posting_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ingestion_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Vector embedding (pgvector) ───────────────────────────────────────────
    # Stored as JSON list for portability; migrate to pgvector Vector type
    # once pgvector extension is confirmed available.
    embedding: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(
        SAEnum(JobStatus, name="job_status_enum"),
        default=JobStatus.active,
        nullable=False,
        index=True,
    )

    dedup_cluster_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_dedup_clusters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    source: Mapped[Optional[JobSource]] = relationship("JobSource", back_populates="jobs")
    dedup_cluster: Mapped[Optional[JobDedupCluster]] = relationship(
        "JobDedupCluster", back_populates="members", foreign_keys=[dedup_cluster_id]
    )
    matches: Mapped[list[JobMatch]] = relationship("JobMatch", back_populates="job")
    applications: Mapped[list[Application]] = relationship("Application", back_populates="job")

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title!r} company={self.company_name!r}>"


# ── JobDedupCluster ───────────────────────────────────────────────────────────


class JobDedupCluster(Base):
    """Groups duplicate job postings from different sources."""

    __tablename__ = "job_dedup_clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    member_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    members: Mapped[list[Job]] = relationship(
        "Job", back_populates="dedup_cluster", foreign_keys="Job.dedup_cluster_id"
    )
    cluster_members: Mapped[list[JobClusterMember]] = relationship(
        "JobClusterMember", back_populates="cluster"
    )


# ── JobClusterMember ──────────────────────────────────────────────────────────


class JobClusterMember(Base):
    """Maps individual jobs to their deduplication cluster with similarity score."""

    __tablename__ = "job_cluster_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_dedup_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cluster: Mapped[JobDedupCluster] = relationship(
        "JobDedupCluster", back_populates="cluster_members"
    )


# ── JobMatch ──────────────────────────────────────────────────────────────────


class JobMatch(Base):
    """Pre-computed match score between a job and a user's profile."""

    __tablename__ = "job_matches"
    __table_args__ = (UniqueConstraint("job_id", "user_id", name="uq_job_match_job_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Scores ────────────────────────────────────────────────────────────────
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    embedding_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    keyword_overlap_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    seniority_fit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_fit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # ── Explanation ───────────────────────────────────────────────────────────
    skill_matches: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    skill_gaps: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    strengths: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Audit ─────────────────────────────────────────────────────────────────
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    job: Mapped[Job] = relationship("Job", back_populates="matches")
    user: Mapped[User] = relationship("User")

    def __repr__(self) -> str:
        return f"<JobMatch job={self.job_id} user={self.user_id} score={self.match_score:.2f}>"
