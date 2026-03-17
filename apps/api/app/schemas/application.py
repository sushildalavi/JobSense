"""
Application Pydantic v2 schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_config

from app.models.application import ApplicationStatus, TriggeredBy


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    notes: Optional[str] = None
    source_of_discovery: Optional[str] = Field(default=None, max_length=255)
    application_url: Optional[str] = None
    cover_letter: Optional[str] = None


class ApplicationUpdate(BaseModel):
    notes: Optional[str] = None
    cover_letter: Optional[str] = None
    application_url: Optional[str] = None
    custom_answers: Optional[Dict[str, Any]] = None
    source_of_discovery: Optional[str] = Field(default=None, max_length=255)
    resume_version_id: Optional[uuid.UUID] = None


class ApplicationEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    application_id: uuid.UUID
    from_status: Optional[ApplicationStatus] = None
    to_status: ApplicationStatus
    triggered_by: TriggeredBy
    notes: Optional[str] = None
    created_at: datetime


class ApplicationListItem(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    source_of_discovery: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Flattened job info
    job_title: Optional[str] = None
    company_name: Optional[str] = None


class ApplicationResponse(ApplicationListItem):
    """Full application detail."""
    resume_version_id: Optional[uuid.UUID] = None
    custom_answers: Optional[Dict[str, Any]] = None
    cover_letter: Optional[str] = None
    application_url: Optional[str] = None
    events: List[ApplicationEventResponse] = Field(default_factory=list)


class StatusTransitionRequest(BaseModel):
    to_status: ApplicationStatus
    triggered_by: TriggeredBy = TriggeredBy.user
    notes: Optional[str] = None


class ApplicationNoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class ApplicationNoteResponse(BaseModel):
    application_id: uuid.UUID
    content: str
    created_at: datetime
