"""
Job service — listing, search, shortlisting, match retrieval.
"""
from __future__ import annotations

import uuid
from typing import List, Optional, Tuple

import structlog
from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobMatch, JobSource, JobStatus
from app.schemas.job import JobFilter

logger = structlog.get_logger(__name__)


class JobService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Job listing ───────────────────────────────────────────────────────────

    async def list_jobs(
        self,
        user_id: uuid.UUID,
        filters: JobFilter,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Job], int]:
        """Return filtered, sorted, paginated jobs with user match scores."""
        query = (
            select(Job)
            .where(Job.status == JobStatus.active)
        )

        # Apply filters
        if filters.is_remote is not None:
            query = query.where(Job.is_remote == filters.is_remote)
        if filters.is_hybrid is not None:
            query = query.where(Job.is_hybrid == filters.is_hybrid)
        if filters.seniority is not None:
            query = query.where(Job.seniority == filters.seniority)
        if filters.employment_type is not None:
            query = query.where(Job.employment_type == filters.employment_type)
        if filters.keyword:
            kw = f"%{filters.keyword}%"
            query = query.where(
                or_(
                    Job.title.ilike(kw),
                    Job.company_name.ilike(kw),
                    Job.cleaned_description.ilike(kw),
                )
            )
        if filters.location:
            loc = f"%{filters.location}%"
            query = query.where(Job.location.ilike(loc))

        # Count before pagination
        count_result = await self.db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar() or 0

        # Sorting
        sort_col = Job.created_at
        if filters.sort_by == "posting_date":
            sort_col = Job.posting_date
        elif filters.sort_by == "match_score":
            # We'll sort in memory after fetching matches
            sort_col = Job.created_at

        if filters.sort_dir == "asc":
            query = query.order_by(sort_col.asc().nullslast())
        else:
            query = query.order_by(sort_col.desc().nullsfirst())

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        jobs = list(result.scalars().all())

        # Attach match scores
        if jobs:
            job_ids = [j.id for j in jobs]
            matches_result = await self.db.execute(
                select(JobMatch).where(
                    JobMatch.job_id.in_(job_ids),
                    JobMatch.user_id == user_id,
                )
            )
            match_map = {m.job_id: m.match_score for m in matches_result.scalars().all()}
            for job in jobs:
                job.match_score = match_map.get(job.id)  # type: ignore[attr-defined]

            if filters.sort_by == "match_score":
                jobs.sort(
                    key=lambda j: getattr(j, "match_score", None) or 0.0,
                    reverse=(filters.sort_dir == "desc"),
                )
            if filters.min_score is not None:
                jobs = [j for j in jobs if (getattr(j, "match_score", None) or 0) >= filters.min_score]

        return jobs, total

    async def list_sources(self) -> List[JobSource]:
        result = await self.db.execute(
            select(JobSource).order_by(JobSource.name.asc())
        )
        return list(result.scalars().all())

    # ── Job detail ────────────────────────────────────────────────────────────

    async def get_job(self, job_id: uuid.UUID) -> Job:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job

    async def get_job_with_match(
        self, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> Tuple[Job, Optional[JobMatch]]:
        job = await self.get_job(job_id)
        match_result = await self.db.execute(
            select(JobMatch).where(
                JobMatch.job_id == job_id,
                JobMatch.user_id == user_id,
            )
        )
        match = match_result.scalar_one_or_none()
        return job, match

    # ── Shortlisting ──────────────────────────────────────────────────────────

    async def shortlist_job(
        self, user_id: uuid.UUID, job_id: uuid.UUID
    ) -> Application:
        """Create or return an Application in 'shortlisted' status."""
        # Ensure job exists
        await self.get_job(job_id)

        # Check for existing
        existing = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.job_id == job_id,
                Application.is_deleted.is_(False),
            )
        )
        app = existing.scalar_one_or_none()
        if app is not None:
            return app

        app = Application(
            user_id=user_id,
            job_id=job_id,
            status=ApplicationStatus.shortlisted,
        )
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def remove_shortlist(self, user_id: uuid.UUID, job_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.job_id == job_id,
                Application.is_deleted.is_(False),
            )
        )
        app = result.scalar_one_or_none()
        if app is not None:
            app.is_deleted = True
            self.db.add(app)
            await self.db.commit()

    # ── Semantic search ───────────────────────────────────────────────────────

    async def search_jobs_semantic(
        self,
        query: str,
        user_id: uuid.UUID,
        limit: int = 20,
        min_score: Optional[float] = None,
    ) -> List[Job]:
        """
        Keyword-based search fallback (semantic search requires pgvector).
        Future: replace with embedding cosine similarity.
        """
        kw = f"%{query}%"
        stmt = (
            select(Job)
            .where(
                Job.status == JobStatus.active,
                or_(
                    Job.title.ilike(kw),
                    Job.cleaned_description.ilike(kw),
                    Job.company_name.ilike(kw),
                ),
            )
            .order_by(Job.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        jobs = list(result.scalars().all())

        # Attach match scores
        if jobs:
            job_ids = [j.id for j in jobs]
            matches_result = await self.db.execute(
                select(JobMatch).where(
                    JobMatch.job_id.in_(job_ids),
                    JobMatch.user_id == user_id,
                )
            )
            match_map = {m.job_id: m.match_score for m in matches_result.scalars().all()}
            for job in jobs:
                job.match_score = match_map.get(job.id)  # type: ignore[attr-defined]

        if min_score is not None:
            jobs = [j for j in jobs if (getattr(j, "match_score", None) or 0) >= min_score]

        return jobs
