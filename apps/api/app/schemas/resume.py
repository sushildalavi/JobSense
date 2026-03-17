"""
Resume Pydantic v2 schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ── Nested parsed resume data structures ─────────────────────────────────────


class WorkExperienceItem(BaseModel):
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    location: Optional[str] = None
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    honors: Optional[str] = None
    relevant_courses: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    bullets: List[str] = Field(default_factory=list)


class CertificationItem(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    credential_id: Optional[str] = None


class SkillsSection(BaseModel):
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud: List[str] = Field(default_factory=list)
    other: List[str] = Field(default_factory=list)


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    website_url: Optional[str] = None


class ParsedResumeData(BaseModel):
    contact: Optional[ContactInfo] = None
    summary: Optional[str] = None
    work_experience: List[WorkExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    skills: Optional[SkillsSection] = None
    certifications: List[CertificationItem] = Field(default_factory=list)
    languages_spoken: List[str] = Field(default_factory=list)
    raw_skills_text: Optional[str] = None
    total_years_experience: Optional[float] = None
    all_skills_flat: List[str] = Field(default_factory=list)


# ── Master resume schemas ──────────────────────────────────────────────────────


class MasterResumeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class MasterResumeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    is_active: Optional[bool] = None


class MasterResumeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    raw_text: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


# ── Resume version schemas ──────────────────────────────────────────────────────


class ResumeVersionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    master_resume_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    tailored_content: Optional[str] = None
    tailored_data: Optional[Dict[str, Any]] = None
    tailoring_strategy: Optional[Dict[str, Any]] = None


class ResumeVersionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    master_resume_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    application_id: Optional[uuid.UUID] = None
    name: str
    tailored_content: Optional[str] = None
    tailored_data: Optional[Dict[str, Any]] = None
    tailoring_strategy: Optional[Dict[str, Any]] = None
    ai_model_used: Optional[str] = None
    prompt_version: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime


# ── Tailoring schemas ──────────────────────────────────────────────────────────


class TailoringRequest(BaseModel):
    resume_id: uuid.UUID
    job_id: uuid.UUID
    strategy_hints: Optional[Dict[str, Any]] = None
    focus_sections: Optional[List[str]] = Field(
        default=None,
        description="Which sections to prioritize: summary, experience, skills, projects",
    )
    max_pages: Optional[int] = Field(default=None, ge=1, le=5)


class TailoringResponse(BaseModel):
    resume_version_id: uuid.UUID
    name: str
    tailored_content: str
    sections_modified: List[str]
    keywords_added: List[str]
    reasoning: str
    ai_model_used: Optional[str] = None
    created_at: datetime
