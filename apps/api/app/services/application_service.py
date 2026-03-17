"""
Application service — CRUD, status transitions, event log.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

import structlog
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationEvent, ApplicationStatus, TriggeredBy
from app.models.job import Job
from app.schemas.application import ApplicationCreate, ApplicationUpdate

logger = structlog.get_logger(__name__)


class ApplicationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_application(self, user_id: uuid.UUID, data: ApplicationCreate) -> Application:
        job = await self.db.get(Job, data.job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

        # Prevent duplicate applications
        existing = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.job_id == data.job_id,
                Application.is_deleted.is_(False),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Application for this job already exists",
            )

        app = Application(
            user_id=user_id,
            job_id=data.job_id,
            notes=data.notes,
            source_of_discovery=data.source_of_discovery,
            application_url=data.application_url,
            cover_letter=data.cover_letter,
            status=ApplicationStatus.discovered,
        )
        self.db.add(app)
        await self.db.flush()

        # Record initial status event
        event = ApplicationEvent(
            application_id=app.id,
            from_status=None,
            to_status=ApplicationStatus.discovered,
            triggered_by=TriggeredBy.user,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def list_applications(
        self,
        user_id: uuid.UUID,
        status_filter: Optional[ApplicationStatus] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Application]:
        query = (
            select(Application)
            .options(selectinload(Application.job))
            .where(
                Application.user_id == user_id,
                Application.is_deleted.is_(False),
            )
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        if status_filter is not None:
            query = query.where(Application.status == status_filter)
        result = await self.db.execute(query)
        apps = list(result.scalars().all())
        # Flatten job title/company
        for app in apps:
            if app.job:
                app.job_title = app.job.title  # type: ignore[attr-defined]
                app.company_name = app.job.company_name  # type: ignore[attr-defined]
        return apps

    async def get_application(self, app_id: uuid.UUID, user_id: uuid.UUID) -> Application:
        result = await self.db.execute(
            select(Application)
            .options(
                selectinload(Application.events),
                selectinload(Application.job),
            )
            .where(
                Application.id == app_id,
                Application.user_id == user_id,
                Application.is_deleted.is_(False),
            )
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
            )
        if app.job:
            app.job_title = app.job.title  # type: ignore[attr-defined]
            app.company_name = app.job.company_name  # type: ignore[attr-defined]
        return app

    async def update_application(
        self,
        app_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ApplicationUpdate,
    ) -> Application:
        app = await self.get_application(app_id, user_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(app, field, value)
        self.db.add(app)
        await self.db.commit()
        await self.db.refresh(app)
        return app

    async def delete_application(self, app_id: uuid.UUID, user_id: uuid.UUID) -> None:
        app = await self.get_application(app_id, user_id)
        app.is_deleted = True
        app.deleted_at = datetime.now(timezone.utc)
        self.db.add(app)
        await self.db.commit()

    async def transition_status(
        self,
        app_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: ApplicationStatus,
        triggered_by: TriggeredBy = TriggeredBy.user,
        notes: Optional[str] = None,
    ) -> ApplicationEvent:
        app = await self.get_application(app_id, user_id)
        old_status = app.status

        app.status = new_status
        if new_status == ApplicationStatus.applied:
            app.applied_at = datetime.now(timezone.utc)

        event = ApplicationEvent(
            application_id=app.id,
            from_status=old_status,
            to_status=new_status,
            triggered_by=triggered_by,
            notes=notes,
        )
        self.db.add(app)
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        logger.info(
            "Application status transitioned",
            app_id=str(app_id),
            from_status=old_status,
            to_status=new_status,
        )
        return event

    async def get_events(self, app_id: uuid.UUID, user_id: uuid.UUID) -> List[ApplicationEvent]:
        # Verify ownership
        await self.get_application(app_id, user_id)
        result = await self.db.execute(
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == app_id)
            .order_by(ApplicationEvent.created_at.asc())
        )
        return list(result.scalars().all())
