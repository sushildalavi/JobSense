"""
Profile service — get/create/update user profiles.
"""

from __future__ import annotations

import uuid
from typing import Union

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate

logger = structlog.get_logger(__name__)


class ProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_or_create_profile(self, user_id: uuid.UUID) -> Profile:
        """Return existing profile or create an empty one."""
        result = await self.db.execute(select(Profile).where(Profile.user_id == user_id))
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = Profile(user_id=user_id)
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)
            logger.info("Profile created", user_id=str(user_id))
        return profile

    async def update_profile(
        self,
        user_id: uuid.UUID,
        data: Union[ProfileCreate, ProfileUpdate],
    ) -> Profile:
        """Upsert or partially update the profile."""
        profile = await self.get_or_create_profile(user_id)

        update_dict = data.model_dump(exclude_none=True)
        for field, value in update_dict.items():
            setattr(profile, field, value)

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        logger.info("Profile updated", user_id=str(user_id), fields=list(update_dict.keys()))
        return profile
