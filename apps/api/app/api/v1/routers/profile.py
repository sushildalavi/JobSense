"""
User profile endpoints.
"""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.services.profile_service import ProfileService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Return the current user's profile, creating one if it doesn't exist."""
    service = ProfileService(db)
    profile = await service.get_or_create_profile(current_user.id)
    return ProfileResponse.model_validate(profile)


@router.put("", response_model=ProfileResponse)
async def upsert_profile(
    data: ProfileCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Fully replace the current user's profile."""
    service = ProfileService(db)
    profile = await service.update_profile(current_user.id, data)
    logger.info("Profile upserted", user_id=str(current_user.id))
    return ProfileResponse.model_validate(profile)


@router.patch("", response_model=ProfileResponse)
async def patch_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Partially update the current user's profile."""
    service = ProfileService(db)
    profile = await service.update_profile(current_user.id, data)
    logger.info("Profile patched", user_id=str(current_user.id))
    return ProfileResponse.model_validate(profile)
