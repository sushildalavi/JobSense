"""
Pydantic schemas for agent outputs.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobMatchOutput(BaseModel):
    match_score: float = Field(ge=0.0, le=1.0)
    skill_matches: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    explanation: str = ""
    model_used: Optional[str] = None
    prompt_version: Optional[str] = None


class ResumeTailoringOutput(BaseModel):
    tailored_content: str
    sections_modified: List[str] = Field(default_factory=list)
    reasoning: str = ""
    keywords_added: List[str] = Field(default_factory=list)
    model_used: Optional[str] = None
    prompt_version: Optional[str] = None


class EmailClassificationOutput(BaseModel):
    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    model_used: Optional[str] = None


class EmailEntityExtractionOutput(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    interviewer: Optional[str] = None
    interview_datetime: Optional[datetime] = None
    timezone: Optional[str] = None
    meeting_link: Optional[str] = None
    next_action: Optional[str] = None
    model_used: Optional[str] = None


class FollowUpDraftOutput(BaseModel):
    subject: str
    body: str
    tone: str = "professional"
    model_used: Optional[str] = None
