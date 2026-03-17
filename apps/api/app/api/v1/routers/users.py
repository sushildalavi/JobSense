"""
User account endpoints.
"""

from __future__ import annotations

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import UserProfile, UserResponse, UserUpdate

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Return the current authenticated user with profile."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.user import User as UserModel

    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.profile))
        .where(UserModel.id == current_user.id)
    )
    user = result.scalar_one()
    return UserProfile.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Partially update the current user's account info."""
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    logger.info("User updated", user_id=str(current_user.id), fields=list(update_data.keys()))
    return UserResponse.model_validate(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete the current user's account."""
    current_user.is_deleted = True
    current_user.is_active = False
    current_user.deleted_at = datetime.now(timezone.utc)
    db.add(current_user)
    await db.commit()
    logger.info("User soft-deleted", user_id=str(current_user.id))


@router.get("/me/integrations")
async def get_integrations(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Return connected integration status for the current user."""
    return {
        "google": {
            "connected": bool(current_user.google_id),
            "gmail": bool(current_user.google_tokens),
            "calendar": bool(current_user.google_tokens),
        },
        "apify": {
            "connected": False,  # managed at platform level
        },
    }
