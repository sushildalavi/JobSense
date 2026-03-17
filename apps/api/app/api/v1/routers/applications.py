"""
Application tracking endpoints.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_active_user,
    get_db,
    get_pagination,
)
from app.models.application import ApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationEventResponse,
    ApplicationListItem,
    ApplicationResponse,
    ApplicationUpdate,
    StatusTransitionRequest,
)
from app.schemas.calendar import CalendarEventResponse
from app.schemas.email import EmailThreadResponse
from app.schemas.resume import ResumeVersionResponse, TailoringRequest
from app.services.application_service import ApplicationService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=List[ApplicationListItem])
async def list_applications(
    app_status: Optional[ApplicationStatus] = Query(default=None, alias="status"),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> List[ApplicationListItem]:
    """List applications with optional status and date range filters."""
    service = ApplicationService(db)
    apps = await service.list_applications(
        user_id=current_user.id,
        status_filter=app_status,
        from_date=from_date,
        to_date=to_date,
        skip=pagination.skip,
        limit=pagination.limit,
    )
    return [ApplicationListItem.model_validate(a) for a in apps]


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Create a new application record."""
    service = ApplicationService(db)
    application = await service.create_application(current_user.id, data)
    logger.info("Application created", app_id=str(application.id), job_id=str(data.job_id))
    return ApplicationResponse.model_validate(application)


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Get full application detail including status history."""
    service = ApplicationService(db)
    application = await service.get_application(app_id, current_user.id)
    return ApplicationResponse.model_validate(application)


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_application(
    app_id: uuid.UUID,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    """Update notes, cover letter, or other mutable fields."""
    service = ApplicationService(db)
    application = await service.update_application(app_id, current_user.id, data)
    return ApplicationResponse.model_validate(application)


@router.delete(
    "/{app_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    response_class=Response,
)
async def delete_application(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete an application."""
    service = ApplicationService(db)
    await service.delete_application(app_id, current_user.id)
    logger.info("Application deleted", app_id=str(app_id))


@router.post("/{app_id}/transition", response_model=ApplicationEventResponse)
async def transition_status(
    app_id: uuid.UUID,
    data: StatusTransitionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ApplicationEventResponse:
    """Change application status and record event."""
    service = ApplicationService(db)
    event = await service.transition_status(
        app_id=app_id,
        user_id=current_user.id,
        new_status=data.to_status,
        triggered_by=data.triggered_by,
        notes=data.notes,
    )
    logger.info(
        "Status transitioned",
        app_id=str(app_id),
        to_status=data.to_status,
        triggered_by=data.triggered_by,
    )
    return ApplicationEventResponse.model_validate(event)


@router.get("/{app_id}/events", response_model=List[ApplicationEventResponse])
async def get_events(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ApplicationEventResponse]:
    """Get the full status-change event history for an application."""
    service = ApplicationService(db)
    events = await service.get_events(app_id, current_user.id)
    return [ApplicationEventResponse.model_validate(e) for e in events]


@router.get("/{app_id}/emails", response_model=List[EmailThreadResponse])
async def get_application_emails(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[EmailThreadResponse]:
    """Get email threads linked to this application."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.email import EmailThread

    result = await db.execute(
        select(EmailThread)
        .options(selectinload(EmailThread.parsed_emails))
        .where(
            EmailThread.application_id == app_id,
            EmailThread.user_id == current_user.id,
        )
    )
    threads = result.scalars().all()
    return [EmailThreadResponse.model_validate(t) for t in threads]


@router.get("/{app_id}/calendar", response_model=List[CalendarEventResponse])
async def get_application_calendar(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[CalendarEventResponse]:
    """Get calendar events linked to this application."""
    from sqlalchemy import select

    from app.models.calendar import CalendarEvent

    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.application_id == app_id,
            CalendarEvent.user_id == current_user.id,
        )
    )
    events = result.scalars().all()
    return [CalendarEventResponse.model_validate(e) for e in events]


@router.post("/{app_id}/tailor-resume", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def tailor_resume_for_application(
    app_id: uuid.UUID,
    data: TailoringRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger resume tailoring for this application (async)."""
    from app.tasks.ai_tasks import tailor_resume

    tailor_resume.delay(str(app_id), str(data.resume_id))
    return {"message": "Resume tailoring triggered", "application_id": str(app_id)}


@router.get("/{app_id}/resume", response_model=ResumeVersionResponse)
async def get_application_resume(
    app_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeVersionResponse:
    """Get the tailored resume version linked to this application."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.application import Application

    result = await db.execute(
        select(Application)
        .options(selectinload(Application.resume_version))
        .where(Application.id == app_id, Application.user_id == current_user.id)
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if application.resume_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No resume version linked"
        )
    return ResumeVersionResponse.model_validate(application.resume_version)
