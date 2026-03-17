"""
Analytics Pydantic v2 schemas.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FunnelStage(BaseModel):
    status: str
    count: int
    percentage: float


class WeeklyStat(BaseModel):
    week_start: date
    applications_count: int
    interviews_count: int
    offers_count: int
    rejections_count: int


class SourceStat(BaseModel):
    source_name: str
    job_count: int
    application_count: int
    avg_match_score: Optional[float] = None


class ScoreBucket(BaseModel):
    bucket_label: str  # e.g. "0-20", "21-40", ...
    min_score: float
    max_score: float
    job_count: int


class DashboardStats(BaseModel):
    total_jobs_tracked: int
    jobs_shortlisted: int
    applications_sent: int
    active_interviews: int
    offers_received: int
    avg_match_score: Optional[float] = None
    response_rate: Optional[float] = None  # applied -> recruiter_contacted / applied
    offer_rate: Optional[float] = None  # offers / applied
    recent_activity: List[Dict] = Field(default_factory=list)


class AnalyticsSummary(BaseModel):
    dashboard: DashboardStats
    funnel: List[FunnelStage]
    weekly: List[WeeklyStat]
    sources: List[SourceStat]
    score_distribution: List[ScoreBucket]
