"""
Email intelligence endpoints.
"""

from __future__ import annotations

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_active_user,
    get_db,
    get_pagination,
)
from app.models.email import EmailThread, ParsedEmail
from app.models.user import User
from app.schemas.email import (
    EmailClassificationResponse,
    EmailSyncRequest,
    EmailThreadResponse,
    ParsedEmailResponse,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("/threads", response_model=List[EmailThreadResponse])
async def list_threads(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> List[EmailThreadResponse]:
    """List email threads for the current user."""
    result = await db.execute(
        select(EmailThread)
        .options(selectinload(EmailThread.parsed_emails))
        .where(EmailThread.user_id == current_user.id)
        .order_by(EmailThread.last_message_at.desc().nullsfirst())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    threads = result.scalars().all()
    return [EmailThreadResponse.model_validate(t) for t in threads]


@router.get("/threads/{thread_id}", response_model=EmailThreadResponse)
async def get_thread(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmailThreadResponse:
    """Get a single thread with all parsed emails."""
    from fastapi import HTTPException

    result = await db.execute(
        select(EmailThread)
        .options(selectinload(EmailThread.parsed_emails))
        .where(EmailThread.id == thread_id, EmailThread.user_id == current_user.id)
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    return EmailThreadResponse.model_validate(thread)


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_emails(
    data: EmailSyncRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger Gmail sync for the current user."""
    from app.tasks.email_tasks import sync_gmail_threads

    sync_gmail_threads.delay(str(current_user.id), data.max_results, data.query)
    logger.info("Email sync triggered", user_id=str(current_user.id))
    return {"message": "Gmail sync triggered", "max_results": data.max_results}


@router.post("/classify", response_model=EmailClassificationResponse)
async def reclassify_thread(
    thread_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> EmailClassificationResponse:
    """Force reclassification of an email thread."""
    from fastapi import HTTPException

    from app.tasks.email_tasks import classify_thread

    result = await db.execute(
        select(EmailThread).where(
            EmailThread.id == thread_id, EmailThread.user_id == current_user.id
        )
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")

    classify_thread.delay(str(thread_id))
    return EmailClassificationResponse(
        thread_id=thread_id,
        classification=thread.classification,
        confidence=thread.confidence_score or 0.0,
        reasoning="Reclassification task triggered",
        updated=True,
    )


@router.get("/parsed", response_model=List[ParsedEmailResponse])
async def list_parsed_emails(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> List[ParsedEmailResponse]:
    """List all parsed email messages for the current user."""
    result = await db.execute(
        select(ParsedEmail)
        .where(ParsedEmail.user_id == current_user.id)
        .order_by(ParsedEmail.received_at.desc().nullsfirst())
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    emails = result.scalars().all()
    return [ParsedEmailResponse.model_validate(e) for e in emails]
