"""
AI-related Celery tasks: resume tailoring, parsing, agent workflows.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
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
    name="app.tasks.ai_tasks.tailor_resume",
    queue="ai",
    max_retries=2,
    default_retry_delay=60,
)
def tailor_resume(self, application_id: str, resume_id: str) -> Dict[str, Any]:
    """Tailor a master resume for the given application's job."""
    logger.info("tailor_resume started", application_id=application_id, resume_id=resume_id)
    try:
        return _run_async(_tailor_resume_async(application_id, resume_id))
    except Exception as exc:
        logger.error("tailor_resume failed", error=str(exc))
        raise self.retry(exc=exc)


async def _tailor_resume_async(application_id: str, resume_id: str) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.agents.workflows.resume_tailoring import run_resume_tailoring_workflow
    from app.core.database import AsyncSessionLocal
    from app.models.application import Application
    from app.models.resume import MasterResume
    from app.services.resume_service import ResumeService

    async with AsyncSessionLocal() as db:
        app_result = await db.execute(
            select(Application).where(Application.id == uuid.UUID(application_id))
        )
        application = app_result.scalar_one_or_none()
        if application is None:
            return {"skipped": True, "reason": "application not found"}

        resume_result = await db.execute(
            select(MasterResume).where(MasterResume.id == uuid.UUID(resume_id))
        )
        master = resume_result.scalar_one_or_none()
        if master is None:
            return {"skipped": True, "reason": "resume not found"}

        from app.models.job import Job

        job_result = await db.execute(select(Job).where(Job.id == application.job_id))
        job = job_result.scalar_one_or_none()
        if job is None:
            return {"skipped": True, "reason": "job not found"}

        output = await run_resume_tailoring_workflow(master, job)

        service = ResumeService(db)
        version = await service.create_resume_version(
            master_resume_id=master.id,
            user_id=master.user_id,
            job_id=job.id,
            application_id=uuid.UUID(application_id),
            tailored_content=output.tailored_content,
            strategy={"sections_modified": output.sections_modified, "reasoning": output.reasoning},
            model_used=output.model_used,
        )

        # Link version to application
        application.resume_version_id = version.id
        db.add(application)
        await db.commit()

    return {"version_id": str(version.id)}


@celery_app.task(
    bind=True,
    name="app.tasks.ai_tasks.parse_resume",
    queue="ai",
    max_retries=2,
    default_retry_delay=30,
)
def parse_resume(self, resume_id: str) -> Dict[str, Any]:
    """Parse a master resume with AI."""
    try:
        return _run_async(_parse_resume_async(resume_id))
    except Exception as exc:
        logger.error("parse_resume failed", error=str(exc))
        raise self.retry(exc=exc)


async def _parse_resume_async(resume_id: str) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.resume import MasterResume
    from app.services.resume_service import ResumeService

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MasterResume).where(MasterResume.id == uuid.UUID(resume_id))
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            return {"skipped": True}

        service = ResumeService(db)
        await service.trigger_parse(resume.id, resume.user_id)
    return {"resume_id": resume_id, "status": "parsed"}


@celery_app.task(
    bind=True,
    name="app.tasks.ai_tasks.run_agent_workflow",
    queue="ai",
    max_retries=2,
    default_retry_delay=60,
)
def run_agent_workflow(
    self,
    workflow_name: str,
    input_data: Dict[str, Any],
    user_id: str,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute a named LangGraph workflow and persist results."""
    logger.info(
        "run_agent_workflow started",
        workflow=workflow_name,
        user_id=user_id,
        run_id=run_id,
    )
    try:
        return _run_async(_run_agent_workflow_async(workflow_name, input_data, user_id, run_id))
    except Exception as exc:
        logger.error("run_agent_workflow failed", workflow=workflow_name, error=str(exc))
        if run_id:
            _run_async(_mark_run_failed(run_id, str(exc)))
        raise self.retry(exc=exc)


async def _run_agent_workflow_async(
    workflow_name: str,
    input_data: Dict[str, Any],
    user_id: str,
    run_id: Optional[str],
) -> Dict[str, Any]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.agent import AgentRun, AgentRunStatus

    start_time = datetime.now(timezone.utc)

    workflow_map = {
        "job_matching": _run_job_matching,
        "resume_tailoring": _run_resume_tailoring,
        "email_classification": _run_email_classification,
        "job_discovery": _run_job_discovery,
    }

    handler = workflow_map.get(workflow_name)
    output_data: Dict[str, Any] = {}
    error_message: Optional[str] = None

    try:
        if handler:
            output_data = await handler(input_data, user_id)
        else:
            output_data = {"skipped": True, "reason": f"Unknown workflow: {workflow_name}"}
    except Exception as exc:
        error_message = str(exc)
        logger.error("Workflow execution error", workflow=workflow_name, error=error_message)

    end_time = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    if run_id:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id)))
            run = result.scalar_one_or_none()
            if run:
                run.status = AgentRunStatus.failed if error_message else AgentRunStatus.completed
                run.output_data = output_data
                run.error_message = error_message
                run.started_at = start_time
                run.completed_at = end_time
                run.duration_ms = duration_ms
                db.add(run)
                await db.commit()

    return {"output": output_data, "duration_ms": duration_ms}


async def _run_job_matching(input_data: Dict, user_id: str) -> Dict:
    from app.tasks.matching import compute_job_matches_for_user

    compute_job_matches_for_user.delay(user_id)
    return {"triggered": True}


async def _run_resume_tailoring(input_data: Dict, user_id: str) -> Dict:
    application_id = input_data.get("application_id")
    resume_id = input_data.get("resume_id")
    if not application_id or not resume_id:
        return {"error": "Missing application_id or resume_id"}
    tailor_resume.delay(application_id, resume_id)
    return {"triggered": True}


async def _run_email_classification(input_data: Dict, user_id: str) -> Dict:
    from app.tasks.email_tasks import sync_gmail_threads

    sync_gmail_threads.delay(user_id)
    return {"triggered": True}


async def _run_job_discovery(input_data: Dict, user_id: str) -> Dict:
    from app.tasks.ingestion import sync_apify_jobs

    sync_apify_jobs.delay(None, user_id)
    return {"triggered": True}


async def _mark_run_failed(run_id: str, error: str) -> None:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.agent import AgentRun, AgentRunStatus

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AgentRun).where(AgentRun.id == uuid.UUID(run_id)))
        run = result.scalar_one_or_none()
        if run:
            run.status = AgentRunStatus.failed
            run.error_message = error
            db.add(run)
            await db.commit()
