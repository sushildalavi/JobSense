"""
Resume endpoints.
"""

from __future__ import annotations

import uuid
from typing import List

import structlog
from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    PaginationParams,
    get_current_active_user,
    get_db,
    get_pagination,
)
from app.models.user import User
from app.schemas.resume import (
    MasterResumeResponse,
    MasterResumeUpdate,
    ResumeVersionResponse,
)
from app.services.resume_service import ResumeService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("", response_model=List[MasterResumeResponse])
async def list_resumes(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination),
) -> List[MasterResumeResponse]:
    """List all master resumes for the current user."""
    service = ResumeService(db)
    resumes = await service.list_resumes(
        current_user.id, skip=pagination.skip, limit=pagination.limit
    )
    return [MasterResumeResponse.model_validate(r) for r in resumes]


@router.post("", response_model=MasterResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    name: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MasterResumeResponse:
    """Upload a new master resume (PDF or DOCX)."""
    service = ResumeService(db)
    resume = await service.create_master_resume(current_user.id, file, name)
    logger.info("Resume created", resume_id=str(resume.id), user_id=str(current_user.id))
    return MasterResumeResponse.model_validate(resume)


@router.get("/{resume_id}", response_model=MasterResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MasterResumeResponse:
    """Get a single master resume by ID."""
    service = ResumeService(db)
    resume = await service.get_resume(resume_id, current_user.id)
    return MasterResumeResponse.model_validate(resume)


@router.patch("/{resume_id}", response_model=MasterResumeResponse)
async def update_resume(
    resume_id: uuid.UUID,
    data: MasterResumeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MasterResumeResponse:
    """Update resume metadata."""
    service = ResumeService(db)
    resume = await service.update_resume(resume_id, current_user.id, data)
    return MasterResumeResponse.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a master resume."""
    service = ResumeService(db)
    await service.delete_resume(resume_id, current_user.id)
    logger.info("Resume deleted", resume_id=str(resume_id))


@router.post("/{resume_id}/parse", response_model=MasterResumeResponse)
async def parse_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> MasterResumeResponse:
    """Trigger AI parsing of the resume text."""
    service = ResumeService(db)
    resume = await service.trigger_parse(resume_id, current_user.id)
    return MasterResumeResponse.model_validate(resume)


@router.get("/{resume_id}/versions", response_model=List[ResumeVersionResponse])
async def list_versions(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ResumeVersionResponse]:
    """List all tailored versions of a master resume."""
    service = ResumeService(db)
    versions = await service.get_resume_versions(resume_id, current_user.id)
    return [ResumeVersionResponse.model_validate(v) for v in versions]


@router.get("/versions/{version_id}", response_model=ResumeVersionResponse)
async def get_version(
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ResumeVersionResponse:
    """Get a specific tailored resume version."""
    service = ResumeService(db)
    version = await service.get_version(version_id, current_user.id)
    return ResumeVersionResponse.model_validate(version)


@router.post("/versions/{version_id}/export-pdf")
async def export_pdf(
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Generate and return a PDF export of a resume version."""
    service = ResumeService(db)
    pdf_bytes = await service.export_version_to_pdf(version_id, current_user.id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=resume_{version_id}.pdf"},
    )
