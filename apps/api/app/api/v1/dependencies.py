"""
FastAPI dependency injection — database session, auth, pagination.
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional

import redis.asyncio as aioredis
import structlog
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import verify_token
from app.models.user import User

logger = structlog.get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


# ── Database session ──────────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Redis ─────────────────────────────────────────────────────────────────────


async def get_redis(request: Request) -> aioredis.Redis:
    """Return the shared Redis client from app state."""
    return request.app.state.redis


# ── Auth ──────────────────────────────────────────────────────────────────────


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Validate JWT bearer token and return the User model.

    Raises 401 if the token is invalid or the user no longer exists.
    """
    token_data = verify_token(token)
    result = await db.execute(
        select(User).where(User.id == token_data.user_id, User.is_deleted.is_(False))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Raises 403 if the user account is deactivated."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    return current_user


async def optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Returns the current user if a valid token is provided, or None.
    Used for endpoints that behave differently for authenticated vs anonymous users.
    """
    if token is None:
        return None
    try:
        token_data = verify_token(token)
    except HTTPException:
        return None
    result = await db.execute(
        select(User).where(User.id == token_data.user_id, User.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


# ── Pagination ─────────────────────────────────────────────────────────────────


class PaginationParams:
    """Reusable pagination dependency."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of items to skip"),
        limit: int = Query(default=20, ge=1, le=200, description="Number of items to return"),
    ):
        self.skip = skip
        self.limit = limit


def get_pagination(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)
