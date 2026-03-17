"""
Analytics service — dashboard stats, funnel, weekly, sources, score distribution.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobMatch, JobSource
from app.schemas.analytics import (
    DashboardStats,
    FunnelStage,
    ScoreBucket,
    SourceStat,
    WeeklyStat,
)

logger = structlog.get_logger(__name__)


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_dashboard_stats(self, user_id: uuid.UUID) -> DashboardStats:
        # Application counts by status
        status_counts_result = await self.db.execute(
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.is_deleted.is_(False),
            )
            .group_by(Application.status)
        )
        status_map = {row.status: row.cnt for row in status_counts_result}

        total_apps = sum(status_map.values())
        shortlisted = status_map.get(ApplicationStatus.shortlisted, 0)
        applied = status_map.get(ApplicationStatus.applied, 0)
        interviews = (
            status_map.get(ApplicationStatus.interview_scheduled, 0)
            + status_map.get(ApplicationStatus.recruiter_contacted, 0)
            + status_map.get(ApplicationStatus.oa_received, 0)
        )
        offers = status_map.get(ApplicationStatus.offer, 0)
        rejections = status_map.get(ApplicationStatus.rejected, 0)

        # Total jobs tracked (jobs with any app)
        jobs_tracked_result = await self.db.execute(
            select(func.count(func.distinct(Application.job_id))).where(
                Application.user_id == user_id,
                Application.is_deleted.is_(False),
            )
        )
        total_jobs_tracked = jobs_tracked_result.scalar() or 0

        # Average match score
        avg_score_result = await self.db.execute(
            select(func.avg(JobMatch.match_score)).where(
                JobMatch.user_id == user_id
            )
        )
        avg_match_score = avg_score_result.scalar()

        response_rate = None
        offer_rate = None
        if applied > 0:
            responded = (
                status_map.get(ApplicationStatus.recruiter_contacted, 0)
                + interviews
                + offers
                + rejections
            )
            response_rate = round(responded / applied, 3)
            offer_rate = round(offers / applied, 3)

        return DashboardStats(
            total_jobs_tracked=total_jobs_tracked,
            jobs_shortlisted=shortlisted,
            applications_sent=applied,
            active_interviews=interviews,
            offers_received=offers,
            avg_match_score=round(avg_match_score, 3) if avg_match_score else None,
            response_rate=response_rate,
            offer_rate=offer_rate,
            recent_activity=[],
        )

    async def get_funnel_data(self, user_id: uuid.UUID) -> List[FunnelStage]:
        status_counts_result = await self.db.execute(
            select(Application.status, func.count(Application.id).label("cnt"))
            .where(
                Application.user_id == user_id,
                Application.is_deleted.is_(False),
            )
            .group_by(Application.status)
        )
        rows = {row.status: row.cnt for row in status_counts_result}
        total = sum(rows.values()) or 1

        funnel_order = [
            ApplicationStatus.discovered,
            ApplicationStatus.shortlisted,
            ApplicationStatus.tailored,
            ApplicationStatus.ready_to_apply,
            ApplicationStatus.applied,
            ApplicationStatus.recruiter_contacted,
            ApplicationStatus.oa_received,
            ApplicationStatus.interview_scheduled,
            ApplicationStatus.offer,
            ApplicationStatus.rejected,
        ]
        result = []
        for s in funnel_order:
            count = rows.get(s, 0)
            result.append(
                FunnelStage(
                    status=s.value,
                    count=count,
                    percentage=round(count / total * 100, 1),
                )
            )
        return result

    async def get_weekly_stats(
        self, user_id: uuid.UUID, weeks: int = 12
    ) -> List[WeeklyStat]:
        today = date.today()
        stats = []
        for w in range(weeks - 1, -1, -1):
            week_start = today - timedelta(days=today.weekday() + w * 7)
            week_end = week_start + timedelta(days=7)

            def _count(s: ApplicationStatus) -> "select":
                return select(func.count(Application.id)).where(
                    Application.user_id == user_id,
                    Application.is_deleted.is_(False),
                    Application.status == s,
                    Application.created_at >= datetime.combine(week_start, datetime.min.time()),
                    Application.created_at < datetime.combine(week_end, datetime.min.time()),
                )

            apps_r = await self.db.execute(_count(ApplicationStatus.applied))
            interviews_r = await self.db.execute(_count(ApplicationStatus.interview_scheduled))
            offers_r = await self.db.execute(_count(ApplicationStatus.offer))
            rejections_r = await self.db.execute(_count(ApplicationStatus.rejected))

            stats.append(
                WeeklyStat(
                    week_start=week_start,
                    applications_count=apps_r.scalar() or 0,
                    interviews_count=interviews_r.scalar() or 0,
                    offers_count=offers_r.scalar() or 0,
                    rejections_count=rejections_r.scalar() or 0,
                )
            )
        return stats

    async def get_source_stats(self, user_id: uuid.UUID) -> List[SourceStat]:
        # Jobs per source
        source_result = await self.db.execute(
            select(
                JobSource.name,
                func.count(Job.id).label("job_count"),
                func.avg(JobMatch.match_score).label("avg_score"),
            )
            .join(Job, Job.source_id == JobSource.id, isouter=True)
            .join(
                JobMatch,
                (JobMatch.job_id == Job.id) & (JobMatch.user_id == user_id),
                isouter=True,
            )
            .group_by(JobSource.name)
            .order_by(func.count(Job.id).desc())
        )
        rows = source_result.all()

        # Applications per source (via job source)
        app_result = await self.db.execute(
            select(JobSource.name, func.count(Application.id).label("app_count"))
            .join(Job, Job.source_id == JobSource.id, isouter=True)
            .join(
                Application,
                (Application.job_id == Job.id) & (Application.user_id == user_id),
                isouter=True,
            )
            .where(Application.is_deleted.is_(False))
            .group_by(JobSource.name)
        )
        app_map = {row.name: row.app_count for row in app_result}

        return [
            SourceStat(
                source_name=row.name,
                job_count=row.job_count or 0,
                application_count=app_map.get(row.name, 0),
                avg_match_score=round(row.avg_score, 3) if row.avg_score else None,
            )
            for row in rows
        ]

    async def get_score_distribution(self, user_id: uuid.UUID) -> List[ScoreBucket]:
        buckets = [
            (0.0, 0.2, "0-20%"),
            (0.2, 0.4, "21-40%"),
            (0.4, 0.6, "41-60%"),
            (0.6, 0.8, "61-80%"),
            (0.8, 1.01, "81-100%"),
        ]
        result = []
        for lo, hi, label in buckets:
            count_result = await self.db.execute(
                select(func.count(JobMatch.id)).where(
                    JobMatch.user_id == user_id,
                    JobMatch.match_score >= lo,
                    JobMatch.match_score < hi,
                )
            )
            result.append(
                ScoreBucket(
                    bucket_label=label,
                    min_score=lo,
                    max_score=hi,
                    job_count=count_result.scalar() or 0,
                )
            )
        return result
