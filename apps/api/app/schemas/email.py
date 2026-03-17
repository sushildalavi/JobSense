"""
Email Pydantic v2 schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, model_config

from app.models.email import EmailClassification


class ParsedEmailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    thread_id: uuid.UUID
    user_id: uuid.UUID
    message_id: str
    subject: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None
    received_at: Optional[datetime] = None
    cleaned_body: Optional[str] = None
    classification: EmailClassification
    confidence_score: Optional[float] = None
    extracted_company: Optional[str] = None
    extracted_job_title: Optional[str] = None
    extracted_interviewer_name: Optional[str] = None
    extracted_interview_datetime: Optional[datetime] = None
    extracted_timezone: Optional[str] = None
    extracted_meeting_link: Optional[str] = None
    extracted_next_action: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    created_at: datetime


class EmailThreadResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    application_id: Optional[uuid.UUID] = None
    thread_id: str
    subject: Optional[str] = None
    participants: Optional[List[str]] = None
    last_message_at: Optional[datetime] = None
    message_count: int
    classification: EmailClassification
    confidence_score: Optional[float] = None
    parsed_emails: List[ParsedEmailResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class EmailSyncRequest(BaseModel):
    max_results: int = 100
    label_ids: Optional[List[str]] = None
    query: Optional[str] = None


class EmailClassificationResponse(BaseModel):
    thread_id: uuid.UUID
    classification: EmailClassification
    confidence: float
    reasoning: str
    updated: bool
