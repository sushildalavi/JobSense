"""
User Pydantic v2 schemas.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_config

from app.schemas.profile import ProfileResponse


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    is_active: bool
    is_verified: bool
    google_id: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserProfile(UserResponse):
    """User response with nested profile data."""
    profile: Optional[ProfileResponse] = None
