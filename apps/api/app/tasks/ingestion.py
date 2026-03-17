"""
Job ingestion Celery tasks.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, Optional

import structlog

from app.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.tasks.ingestion.sync_apify_jobs",
    queue="ingestion",
    max_retries=3,
    default_retry_delay=120,
)
def sync_apify_jobs(
    self,
    source_id: Optional[str],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Trigger Apify actor run for one or all active job sources.
    Enqueues process_raw_job for each result.
    """
    logger.info("sync_apify_jobs started", source_id=source_id, user_id=user_id)
    try:
        return _run_async(_sync_apify_jobs_async(source_id, user_id))
    except Exception as exc:
        logger.error("sync_apify_jobs failed", error=str(exc))
        raise self.retry(exc=exc)


async def _sync_apify_jobs_async(
    source_id: Optional[str], user_id: Optional[str]
) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.integrations.apify.client import ApifyClient
    from app.models.job import JobSource

    async with AsyncSessionLocal() as db:
        if source_id:
            result = await db.execute(select(JobSource).where(JobSource.id == uuid.UUID(source_id)))
            sources = [result.scalar_one_or_none()]
            sources = [s for s in sources if s is not None]
        else:
            result = await db.execute(select(JobSource).where(JobSource.is_active.is_(True)))
            sources = list(result.scalars().all())

        total_ingested = 0
        client = ApifyClient()

        for source in sources:
            if source.connector_type != "apify":
                continue
            config = source.config or {}
            actor_id = config.get("actor_id")
            actor_input = config.get("input", {})
            if not actor_id:
                continue

            try:
                raw_jobs = await client.run_actor(actor_id, actor_input)
                for raw_job in raw_jobs:
                    process_raw_job.delay(raw_job, str(source.id))
                    total_ingested += 1

                from datetime import datetime, timezone

                source.last_synced_at = datetime.now(timezone.utc)
                db.add(source)

            except Exception as exc:
                logger.error("Apify actor run failed", source=source.name, error=str(exc))
                continue

        await db.commit()

    logger.info("sync_apify_jobs completed", total=total_ingested)
    return {"ingested": total_ingested}


@celery_app.task(
    bind=True,
    name="app.tasks.ingestion.process_raw_job",
    queue="ingestion",
    max_retries=3,
    default_retry_delay=30,
)
def process_raw_job(
    self,
    raw_job_data: Dict[str, Any],
    source_id: str,
) -> Dict[str, Any]:
    """Normalize a raw Apify job record and upsert into the database."""
    try:
        return _run_async(_process_raw_job_async(raw_job_data, source_id))
    except Exception as exc:
        logger.error("process_raw_job failed", error=str(exc))
        raise self.retry(exc=exc)


async def _process_raw_job_async(raw_job_data: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.integrations.apify.normalizer import normalize_apify_job
    from app.models.job import Job

    normalized = normalize_apify_job(raw_job_data, source_id=source_id)
    if normalized is None:
        return {"skipped": True}

    async with AsyncSessionLocal() as db:
        # Dedup check
        existing = await db.execute(
            select(Job).where(
                Job.source_id == uuid.UUID(source_id),
                Job.source_job_id == normalized["source_job_id"],
            )
        )
        job = existing.scalar_one_or_none()

        if job is None:
            job = Job(**normalized, source_id=uuid.UUID(source_id))
            db.add(job)
            action = "created"
        else:
            # Update mutable fields
            for field in ("title", "cleaned_description", "salary_min", "salary_max", "status"):
                if field in normalized:
                    setattr(job, field, normalized[field])
            action = "updated"

        await db.commit()
        return {"action": action, "job_id": str(job.id)}


@celery_app.task(
    name="app.tasks.ingestion.run_deduplication",
    queue="ingestion",
)
def run_deduplication() -> Dict[str, Any]:
    """Run deduplication pass across all active jobs."""
    logger.info("run_deduplication started")
    # Future: compare embeddings across jobs to cluster duplicates
    return {"status": "completed", "clusters_updated": 0}
