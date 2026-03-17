"""
Authentication endpoints.
"""
from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user, get_db, get_redis
from app.models.user import User
from app.schemas.auth import (
    GoogleOAuthCallback,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user and return an access token."""
    service = AuthService(db)
    user, token_response = await service.register_user(data)
    logger.info("New user registered", user_id=str(user.id), email=user.email)
    return token_response


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticate with email + password and return tokens."""
    service = AuthService(db)
    user = await service.authenticate_user(data.email, data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_response = await service.create_tokens(user)
    logger.info("User logged in", user_id=str(user.id))
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a refresh token for a new access token."""
    service = AuthService(db)
    token_response = await service.refresh_access_token(data.refresh_token)
    return token_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Invalidate the current user's session."""
    logger.info("User logged out", user_id=str(current_user.id))


@router.get("/google")
async def google_oauth_initiate() -> RedirectResponse:
    """Initiate Google OAuth flow — redirect to Google's consent screen."""
    service = AuthService(None)  # type: ignore[arg-type]
    url = service.get_google_oauth_url()
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback", response_model=TokenResponse)
async def google_oauth_callback(
    code: str,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Handle Google OAuth callback, upsert user, return tokens."""
    service = AuthService(db)
    user, token_response = await service.handle_google_callback(code, state)
    logger.info("Google OAuth callback", user_id=str(user.id))
    return token_response


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Send password reset email (fire-and-forget)."""
    service = AuthService(db)
    background_tasks.add_task(service.initiate_password_reset, data.email)
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Complete password reset using token from email."""
    service = AuthService(db)
    await service.reset_password(data.token, data.new_password)
    return {"message": "Password has been reset successfully."}
