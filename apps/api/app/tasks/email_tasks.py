"""
Email processing Celery tasks.
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
    name="app.tasks.email_tasks.sync_gmail_threads",
    queue="email",
    max_retries=3,
    default_retry_delay=60,
)
def sync_gmail_threads(
    self,
    user_id: str,
    max_results: int = 100,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """Sync recruiting-related Gmail threads for a user."""
    logger.info("sync_gmail_threads started", user_id=user_id)
    try:
        return _run_async(_sync_gmail_threads_async(user_id, max_results, query))
    except Exception as exc:
        logger.error("sync_gmail_threads failed", user_id=user_id, error=str(exc))
        raise self.retry(exc=exc)


async def _sync_gmail_threads_async(
    user_id: str, max_results: int, query: Optional[str]
) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.integrations.gmail.client import GmailClient
    from app.integrations.gmail.filters import is_recruiting_related
    from app.models.email import EmailClassification, EmailThread
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if user is None or not user.google_tokens:
            return {"skipped": True, "reason": "no google tokens"}

        client = GmailClient(user.google_tokens)
        threads_data = await client.list_threads(
            max_results=max_results,
            query=query or "subject:(interview OR offer OR application OR recruiter OR job)",
        )

        ingested = 0
        for thread_data in threads_data:
            gmail_thread_id = thread_data.get("id")
            if not gmail_thread_id:
                continue

            # Check if thread already exists
            existing = await db.execute(
                select(EmailThread).where(
                    EmailThread.thread_id == gmail_thread_id,
                    EmailThread.user_id == uuid.UUID(user_id),
                )
            )
            thread_record = existing.scalar_one_or_none()

            parsed = await client.get_thread(gmail_thread_id)
            if not parsed:
                continue

            if not is_recruiting_related(parsed):
                continue

            if thread_record is None:
                thread_record = EmailThread(
                    user_id=uuid.UUID(user_id),
                    thread_id=gmail_thread_id,
                    subject=parsed.get("subject"),
                    participants=parsed.get("participants", []),
                    last_message_at=parsed.get("last_message_at"),
                    message_count=parsed.get("message_count", 1),
                    classification=EmailClassification.unclassified,
                )
                db.add(thread_record)
                await db.flush()
                ingested += 1

            # Classify asynchronously
            classify_thread.delay(str(thread_record.id))

        await db.commit()

    logger.info("sync_gmail_threads completed", user_id=user_id, ingested=ingested)
    return {"ingested": ingested}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.classify_thread",
    queue="email",
    max_retries=3,
    default_retry_delay=30,
)
def classify_thread(self, thread_id: str) -> Dict[str, Any]:
    """Run AI classification on an email thread."""
    try:
        return _run_async(_classify_thread_async(thread_id))
    except Exception as exc:
        logger.error("classify_thread failed", thread_id=thread_id, error=str(exc))
        raise self.retry(exc=exc)


async def _classify_thread_async(thread_id: str) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.agents.workflows.email_classification import run_email_classification_workflow
    from app.core.database import AsyncSessionLocal
    from app.models.email import EmailThread

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(EmailThread).where(EmailThread.id == uuid.UUID(thread_id)))
        thread = result.scalar_one_or_none()
        if thread is None:
            return {"skipped": True}

        # Get thread content from DB or use subject as content
        content = thread.subject or ""
        output = await run_email_classification_workflow(content, thread_id=thread_id)

        thread.classification = output.classification
        thread.confidence_score = output.confidence
        db.add(thread)

        # Extract entities
        extract_email_entities.delay(thread_id)

        await db.commit()

    return {
        "thread_id": thread_id,
        "classification": output.classification.value,
        "confidence": output.confidence,
    }


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.extract_email_entities",
    queue="email",
    max_retries=2,
    default_retry_delay=30,
)
def extract_email_entities(self, thread_id: str) -> Dict[str, Any]:
    """Extract structured entities (company, interviewer, datetime) from email."""
    try:
        return _run_async(_extract_entities_async(thread_id))
    except Exception as exc:
        logger.error("extract_email_entities failed", error=str(exc))
        raise self.retry(exc=exc)


async def _extract_entities_async(thread_id: str) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.agents.workflows.email_classification import run_entity_extraction_workflow
    from app.core.database import AsyncSessionLocal
    from app.models.email import EmailThread, ParsedEmail

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(EmailThread).where(EmailThread.id == uuid.UUID(thread_id)))
        thread = result.scalar_one_or_none()
        if thread is None:
            return {"skipped": True}

        content = thread.subject or ""
        entities = await run_entity_extraction_workflow(content)

        # Create ParsedEmail record
        parsed = ParsedEmail(
            thread_id=thread.id,
            user_id=thread.user_id,
            message_id=f"extracted_{thread_id}",
            classification=thread.classification,
            extracted_company=entities.company,
            extracted_job_title=entities.job_title,
            extracted_interviewer_name=entities.interviewer,
            extracted_interview_datetime=entities.interview_datetime,
            extracted_timezone=entities.timezone,
            extracted_meeting_link=entities.meeting_link,
            extracted_next_action=entities.next_action,
        )
        db.add(parsed)
        await db.commit()
        await db.refresh(parsed)

        # Trigger calendar creation if interview found
        if entities.interview_datetime:
            from app.tasks.calendar_tasks import create_interview_event

            create_interview_event.delay(str(parsed.id), str(thread.user_id))

        # Link to application
        link_email_to_application.delay(thread_id, str(thread.user_id))

    return {"extracted": True}


@celery_app.task(
    bind=True,
    name="app.tasks.email_tasks.link_email_to_application",
    queue="email",
    max_retries=2,
    default_retry_delay=30,
)
def link_email_to_application(self, thread_id: str, user_id: str) -> Dict[str, Any]:
    """Try to link an email thread to an existing application."""
    try:
        return _run_async(_link_email_async(thread_id, user_id))
    except Exception as exc:
        logger.error("link_email_to_application failed", error=str(exc))
        raise self.retry(exc=exc)


async def _link_email_async(thread_id: str, user_id: str) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.application import Application
    from app.models.email import EmailThread, ParsedEmail
    from app.models.job import Job

    async with AsyncSessionLocal() as db:
        # Get thread with extracted entity
        result = await db.execute(select(EmailThread).where(EmailThread.id == uuid.UUID(thread_id)))
        thread = result.scalar_one_or_none()
        if thread is None or thread.application_id is not None:
            return {"skipped": True}

        # Get extracted company name
        parsed_result = await db.execute(
            select(ParsedEmail)
            .where(
                ParsedEmail.thread_id == thread.id,
                ParsedEmail.extracted_company.isnot(None),
            )
            .limit(1)
        )
        parsed = parsed_result.scalar_one_or_none()
        if parsed is None or not parsed.extracted_company:
            return {"no_match": True}

        # Find matching application by company
        app_result = await db.execute(
            select(Application)
            .join(Job, Application.job_id == Job.id)
            .where(
                Application.user_id == uuid.UUID(user_id),
                Application.is_deleted.is_(False),
                Job.company_name.ilike(f"%{parsed.extracted_company}%"),
            )
            .limit(1)
        )
        app = app_result.scalar_one_or_none()
        if app:
            thread.application_id = app.id
            db.add(thread)
            await db.commit()
            return {"linked": True, "application_id": str(app.id)}

    return {"no_match": True}
