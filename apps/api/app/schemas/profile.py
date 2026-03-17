"""
User Profile Pydantic v2 schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_config

from app.models.profile import RemotePreference, SeniorityLevel


class ProfileCreate(BaseModel):
    target_roles: Optional[List[str]] = Field(default_factory=list)
    preferred_locations: Optional[List[str]] = Field(default_factory=list)
    remote_preference: Optional[RemotePreference] = None
    seniority_level: Optional[SeniorityLevel] = None
    preferred_industries: Optional[List[str]] = Field(default_factory=list)
    years_of_experience: Optional[int] = Field(default=None, ge=0, le=60)

    visa_status: Optional[str] = Field(default=None, max_length=100)
    work_authorization: Optional[str] = Field(default=None, max_length=100)

    preferred_salary_min: Optional[int] = Field(default=None, ge=0)
    preferred_salary_max: Optional[int] = Field(default=None, ge=0)
    preferred_currency: str = Field(default="USD", max_length=10)

    skills: Optional[List[str]] = Field(default_factory=list)
    keywords_to_prioritize: Optional[List[str]] = Field(default_factory=list)
    keywords_to_avoid: Optional[List[str]] = Field(default_factory=list)

    linkedin_url: Optional[str] = Field(default=None, max_length=512)
    github_url: Optional[str] = Field(default=None, max_length=512)
    portfolio_url: Optional[str] = Field(default=None, max_length=512)

    @field_validator("preferred_salary_max")
    @classmethod
    def validate_salary_range(cls, v: Optional[int], info) -> Optional[int]:
        if v is not None and info.data.get("preferred_salary_min") is not None:
            if v < info.data["preferred_salary_min"]:
                raise ValueError("preferred_salary_max must be >= preferred_salary_min")
        return v


class ProfileUpdate(BaseModel):
    """All fields optional for PATCH operations."""
    target_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    remote_preference: Optional[RemotePreference] = None
    seniority_level: Optional[SeniorityLevel] = None
    preferred_industries: Optional[List[str]] = None
    years_of_experience: Optional[int] = Field(default=None, ge=0, le=60)

    visa_status: Optional[str] = Field(default=None, max_length=100)
    work_authorization: Optional[str] = Field(default=None, max_length=100)

    preferred_salary_min: Optional[int] = Field(default=None, ge=0)
    preferred_salary_max: Optional[int] = Field(default=None, ge=0)
    preferred_currency: Optional[str] = Field(default=None, max_length=10)

    skills: Optional[List[str]] = None
    keywords_to_prioritize: Optional[List[str]] = None
    keywords_to_avoid: Optional[List[str]] = None

    linkedin_url: Optional[str] = Field(default=None, max_length=512)
    github_url: Optional[str] = Field(default=None, max_length=512)
    portfolio_url: Optional[str] = Field(default=None, max_length=512)


class ProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID

    target_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    remote_preference: Optional[RemotePreference] = None
    seniority_level: Optional[SeniorityLevel] = None
    preferred_industries: Optional[List[str]] = None
    years_of_experience: Optional[int] = None

    visa_status: Optional[str] = None
    work_authorization: Optional[str] = None

    preferred_salary_min: Optional[int] = None
    preferred_salary_max: Optional[int] = None
    preferred_currency: str = "USD"

    skills: Optional[List[str]] = None
    keywords_to_prioritize: Optional[List[str]] = None
    keywords_to_avoid: Optional[List[str]] = None

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime] = None
