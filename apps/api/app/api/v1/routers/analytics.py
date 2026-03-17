"""
Analytics endpoints.
"""

from __future__ import annotations

from typing import List

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.agent import AgentRunResponse
from app.schemas.analytics import (
    DashboardStats,
    FunnelStage,
    ScoreBucket,
    SourceStat,
    WeeklyStat,
)
from app.services.analytics_service import AnalyticsService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardStats:
    """Return high-level dashboard KPIs."""
    service = AnalyticsService(db)
    return await service.get_dashboard_stats(current_user.id)


@router.get("/funnel", response_model=List[FunnelStage])
async def funnel(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[FunnelStage]:
    """Return application pipeline funnel breakdown."""
    service = AnalyticsService(db)
    return await service.get_funnel_data(current_user.id)


@router.get("/sources", response_model=List[SourceStat])
async def sources(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[SourceStat]:
    """Return jobs-by-source breakdown."""
    service = AnalyticsService(db)
    return await service.get_source_stats(current_user.id)


@router.get("/weekly", response_model=List[WeeklyStat])
async def weekly(
    weeks: int = Query(default=12, ge=1, le=52),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[WeeklyStat]:
    """Return weekly applications, interviews, offers, rejections."""
    service = AnalyticsService(db)
    return await service.get_weekly_stats(current_user.id, weeks=weeks)


@router.get("/match-scores", response_model=List[ScoreBucket])
async def match_scores(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ScoreBucket]:
    """Return distribution of match scores across all jobs."""
    service = AnalyticsService(db)
    return await service.get_score_distribution(current_user.id)


@router.get("/agent-runs", response_model=List[AgentRunResponse])
async def agent_runs(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[AgentRunResponse]:
    """Return recent AI agent run history."""
    from sqlalchemy import select

    from app.models.agent import AgentRun

    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    return [AgentRunResponse.model_validate(r) for r in runs]
