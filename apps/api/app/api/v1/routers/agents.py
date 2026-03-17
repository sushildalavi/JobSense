"""
AI Agent workflow endpoints.
"""

from __future__ import annotations

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_active_user,
    get_db,
    get_pagination,
)
from app.models.agent import AgentRun, AgentRunStatus
from app.models.user import User
from app.schemas.agent import AgentRunResponse, WorkflowTriggerRequest

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_workflow(
    data: WorkflowTriggerRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AgentRunResponse:
    """Trigger an AI workflow and return the created AgentRun record."""
    # Create the run record
    run = AgentRun(
        user_id=current_user.id,
        workflow_name=data.workflow_name,
        status=AgentRunStatus.pending,
        input_data=data.input_data,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Dispatch Celery task
    if data.async_execution:
        from app.tasks.ai_tasks import run_agent_workflow

        run_agent_workflow.delay(
            data.workflow_name.value,
            data.input_data or {},
            str(current_user.id),
            str(run.id),
        )

    logger.info(
        "Agent workflow triggered",
        workflow=data.workflow_name,
        run_id=str(run.id),
        user_id=str(current_user.id),
    )
    return AgentRunResponse.model_validate(run)


@router.get("/runs", response_model=List[AgentRunResponse])
async def list_runs(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> List[AgentRunResponse]:
    """List agent run history for the current user."""
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.user_id == current_user.id)
        .order_by(AgentRun.created_at.desc())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    runs = result.scalars().all()
    return [AgentRunResponse.model_validate(r) for r in runs]


@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_run(
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> AgentRunResponse:
    """Get detail of a specific agent run."""
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return AgentRunResponse.model_validate(run)
