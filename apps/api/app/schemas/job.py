"""
Job-related Pydantic v2 schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.job import EmploymentType, JobSeniority, JobStatus

# ── Job source ────────────────────────────────────────────────────────────────


class JobSourceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    connector_type: str
    is_active: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime


# ── Job match ─────────────────────────────────────────────────────────────────


class JobMatchResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    job_id: uuid.UUID
    user_id: uuid.UUID
    match_score: float
    embedding_similarity: Optional[float] = None
    keyword_overlap_score: Optional[float] = None
    seniority_fit: Optional[float] = None
    location_fit: Optional[float] = None
    skill_matches: Optional[List[str]] = None
    skill_gaps: Optional[List[str]] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    explanation: Optional[str] = None
    computed_at: datetime
    model_used: Optional[str] = None


# ── Job list / detail ─────────────────────────────────────────────────────────


class JobListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    title: str
    company_name: str
    location: Optional[str] = None
    is_remote: bool
    is_hybrid: bool
    employment_type: Optional[EmploymentType] = None
    seniority: Optional[JobSeniority] = None
    salary_text: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    posting_date: Optional[datetime] = None
    status: JobStatus
    apply_url: Optional[str] = None
    match_score: Optional[float] = None
    created_at: datetime


class JobResponse(JobListItem):
    """Full job detail including description and match info."""

    company_website: Optional[str] = None
    raw_description: Optional[str] = None
    cleaned_description: Optional[str] = None
    requirements: Optional[List[str]] = None
    preferred_qualifications: Optional[List[str]] = None
    responsibilities: Optional[List[str]] = None
    source_id: Optional[uuid.UUID] = None
    source_job_id: Optional[str] = None
    ingestion_timestamp: Optional[datetime] = None
    match: Optional[JobMatchResponse] = None


# ── Job filters & search ──────────────────────────────────────────────────────


class JobFilter(BaseModel):
    """Query parameters for job listing endpoint."""

    source: Optional[str] = None
    status: Optional[JobStatus] = None
    is_remote: Optional[bool] = None
    is_hybrid: Optional[bool] = None
    seniority: Optional[JobSeniority] = None
    employment_type: Optional[EmploymentType] = None
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    keyword: Optional[str] = None
    location: Optional[str] = None
    sort_by: str = Field(
        default="ingested_at", description="match_score | posting_date | ingested_at"
    )
    sort_dir: str = Field(default="desc", description="asc | desc")


class JobSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)
    min_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class JobRankingResponse(BaseModel):
    """Ranked list of jobs with match scores."""

    jobs: List[JobListItem]
    total: int
    query: Optional[str] = None
