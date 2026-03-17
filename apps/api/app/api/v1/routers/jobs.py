"""
Job endpoints.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_active_user,
    get_db,
    get_pagination,
)
from app.models.job import EmploymentType, JobSeniority, JobStatus
from app.models.user import User
from app.schemas.job import (
    JobFilter,
    JobListItem,
    JobMatchResponse,
    JobRankingResponse,
    JobResponse,
    JobSourceResponse,
)
from app.services.job_service import JobService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobRankingResponse)
async def list_jobs(
    source: Optional[str] = Query(default=None),
    job_status: Optional[JobStatus] = Query(default=None, alias="status"),
    is_remote: Optional[bool] = Query(default=None),
    is_hybrid: Optional[bool] = Query(default=None),
    seniority: Optional[JobSeniority] = Query(default=None),
    employment_type: Optional[EmploymentType] = Query(default=None),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    keyword: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    sort_by: str = Query(default="ingested_at"),
    sort_dir: str = Query(default="desc"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> JobRankingResponse:
    """List jobs with filtering, sorting, and pagination."""
    filters = JobFilter(
        source=source,
        status=job_status,
        is_remote=is_remote,
        is_hybrid=is_hybrid,
        seniority=seniority,
        employment_type=employment_type,
        min_score=min_score,
        keyword=keyword,
        location=location,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    service = JobService(db)
    jobs, total = await service.list_jobs(
        current_user.id, filters, skip=pagination.skip, limit=pagination.limit
    )
    return JobRankingResponse(
        jobs=[JobListItem.model_validate(j) for j in jobs],
        total=total,
    )


@router.get("/sources", response_model=List[JobSourceResponse])
async def list_sources(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[JobSourceResponse]:
    """List all configured job sources."""
    service = JobService(db)
    sources = await service.list_sources()
    return [JobSourceResponse.model_validate(s) for s in sources]


@router.get("/search", response_model=JobRankingResponse)
async def semantic_search(
    q: str = Query(min_length=1, max_length=500),
    limit: int = Query(default=20, ge=1, le=100),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> JobRankingResponse:
    """Semantic search across job descriptions using embeddings."""
    service = JobService(db)
    jobs = await service.search_jobs_semantic(
        query=q,
        user_id=current_user.id,
        limit=limit,
        min_score=min_score,
    )
    return JobRankingResponse(
        jobs=[JobListItem.model_validate(j) for j in jobs],
        total=len(jobs),
        query=q,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get full job detail with match information."""
    service = JobService(db)
    job, match = await service.get_job_with_match(job_id, current_user.id)
    response = JobResponse.model_validate(job)
    if match:
        response.match = JobMatchResponse.model_validate(match)
    return response


@router.post("/{job_id}/shortlist", response_model=dict, status_code=status.HTTP_201_CREATED)
async def shortlist_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a job to shortlist (creates an Application record in 'shortlisted' status)."""
    service = JobService(db)
    application = await service.shortlist_job(current_user.id, job_id)
    logger.info("Job shortlisted", job_id=str(job_id), application_id=str(application.id))
    return {"application_id": str(application.id), "status": application.status}


@router.delete("/{job_id}/shortlist", status_code=status.HTTP_204_NO_CONTENT)
async def remove_shortlist(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a job from shortlist."""
    service = JobService(db)
    await service.remove_shortlist(current_user.id, job_id)


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_jobs(
    source_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger Apify job ingestion for one or all sources."""
    from app.tasks.ingestion import sync_apify_jobs

    sync_apify_jobs.delay(str(source_id) if source_id else None, str(current_user.id))
    return {"message": "Job sync triggered", "source_id": str(source_id) if source_id else "all"}


@router.post("/{job_id}/match", response_model=JobMatchResponse)
async def compute_match(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> JobMatchResponse:
    """Compute or recompute match score for a job."""
    from app.tasks.matching import compute_single_match

    compute_single_match.delay(str(job_id), str(current_user.id))
    service = JobService(db)
    _, match = await service.get_job_with_match(job_id, current_user.id)
    if match is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not yet computed")
    return JobMatchResponse.model_validate(match)
