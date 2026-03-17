"""
Job-matching Celery tasks.
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.tasks.matching.compute_job_matches_for_user",
    queue="matching",
    max_retries=2,
    default_retry_delay=60,
)
def compute_job_matches_for_user(self, user_id: str) -> Dict[str, Any]:
    """Compute match scores for all active jobs for a given user."""
    logger.info("compute_job_matches_for_user started", user_id=user_id)
    try:
        return _run_async(_compute_matches_for_user_async(user_id))
    except Exception as exc:
        logger.error("compute_job_matches_for_user failed", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc)


async def _compute_matches_for_user_async(user_id: str) -> Dict[str, Any]:
    from app.core.database import AsyncSessionLocal
    from app.models.job import Job, JobMatch, JobStatus
    from app.models.profile import Profile
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get user profile
        result = await db.execute(
            select(Profile).where(Profile.user_id == uuid.UUID(user_id))
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            return {"skipped": True, "reason": "no profile"}

        # Get active jobs without existing match
        result = await db.execute(
            select(Job).where(Job.status == JobStatus.active).limit(500)
        )
        jobs = result.scalars().all()

        count = 0
        for job in jobs:
            compute_single_match.delay(str(job.id), user_id)
            count += 1

    return {"dispatched": count}


@celery_app.task(
    bind=True,
    name="app.tasks.matching.compute_single_match",
    queue="matching",
    max_retries=3,
    default_retry_delay=30,
)
def compute_single_match(self, job_id: str, user_id: str) -> Dict[str, Any]:
    """Compute or recompute match score for a single job+user pair."""
    try:
        return _run_async(_compute_single_match_async(job_id, user_id))
    except Exception as exc:
        logger.error("compute_single_match failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc)


async def _compute_single_match_async(job_id: str, user_id: str) -> Dict[str, Any]:
    from app.core.database import AsyncSessionLocal
    from app.models.job import Job, JobMatch
    from app.models.profile import Profile
    from app.agents.workflows.job_matching import run_job_matching_workflow
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        job_result = await db.execute(select(Job).where(Job.id == uuid.UUID(job_id)))
        job = job_result.scalar_one_or_none()
        if job is None:
            return {"skipped": True, "reason": "job not found"}

        profile_result = await db.execute(
            select(Profile).where(Profile.user_id == uuid.UUID(user_id))
        )
        profile = profile_result.scalar_one_or_none()
        if profile is None:
            return {"skipped": True, "reason": "no profile"}

        # Run matching workflow
        output = await run_job_matching_workflow(job, profile)

        # Upsert JobMatch
        existing_result = await db.execute(
            select(JobMatch).where(
                JobMatch.job_id == uuid.UUID(job_id),
                JobMatch.user_id == uuid.UUID(user_id),
            )
        )
        match = existing_result.scalar_one_or_none()

        if match is None:
            match = JobMatch(
                job_id=uuid.UUID(job_id),
                user_id=uuid.UUID(user_id),
            )

        match.match_score = output.match_score
        match.skill_matches = output.skill_matches
        match.skill_gaps = output.skill_gaps
        match.explanation = output.explanation
        match.model_used = output.model_used

        db.add(match)
        await db.commit()

    return {"match_score": output.match_score, "job_id": job_id, "user_id": user_id}


@celery_app.task(
    name="app.tasks.matching.recompute_all_matches",
    queue="matching",
)
def recompute_all_matches() -> Dict[str, Any]:
    """Fan out match computation for all active users."""
    return _run_async(_recompute_all_async())


async def _recompute_all_async() -> Dict[str, Any]:
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User.id).where(User.is_active.is_(True), User.is_deleted.is_(False))
        )
        user_ids = [str(row[0]) for row in result.all()]

    for uid in user_ids:
        compute_job_matches_for_user.delay(uid)

    return {"dispatched": len(user_ids)}
