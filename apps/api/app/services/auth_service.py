"""
Authentication service — registration, login, OAuth, tokens.
"""
from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import structlog
from fastapi import HTTPException, status
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.models.profile import Profile
from app.schemas.auth import RegisterRequest, TokenResponse

logger = structlog.get_logger(__name__)

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar",
]

# Refresh token TTL (30 days)
REFRESH_TOKEN_EXPIRE_DAYS = 30


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Registration ──────────────────────────────────────────────────────────

    async def register_user(self, data: RegisterRequest) -> Tuple[User, TokenResponse]:
        """Create a new user + profile and issue tokens."""
        # Check uniqueness
        existing = await self.db.execute(
            select(User).where(User.email == data.email, User.is_deleted.is_(False))
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=get_password_hash(data.password),
            is_active=True,
            is_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        # Create empty profile
        profile = Profile(user_id=user.id)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(user)

        token_response = await self.create_tokens(user)
        return user, token_response

    # ── Authentication ────────────────────────────────────────────────────────

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Verify credentials; returns User or None."""
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()
        if user is None:
            return None
        if user.hashed_password is None:
            # OAuth-only account
            return None
        if not verify_password(password, user.hashed_password):
            return None

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        self.db.add(user)
        await self.db.commit()
        return user

    # ── Token management ──────────────────────────────────────────────────────

    async def create_tokens(self, user: User) -> TokenResponse:
        """Issue an access token and refresh token for a user."""
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = self._create_refresh_token(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    def _create_refresh_token(self, user: User) -> str:
        """Create a long-lived signed refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        data = {
            "sub": str(user.id),
            "email": user.email,
            "type": "refresh",
            "exp": expire,
        }
        return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Validate refresh token and issue a new access token."""
        try:
            payload = jwt.decode(
                refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "refresh":
                raise ValueError("Not a refresh token")
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            ) from exc

        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        return await self.create_tokens(user)

    # ── Google OAuth ──────────────────────────────────────────────────────────

    def get_google_oauth_url(self) -> str:
        """Build the Google OAuth2 authorization URL."""
        flow = self._build_oauth_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    async def handle_google_callback(
        self, code: str, state: Optional[str]
    ) -> Tuple[User, TokenResponse]:
        """Exchange authorization code for tokens, upsert user."""
        flow = self._build_oauth_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Fetch profile from Google
        service = build("oauth2", "v2", credentials=credentials)
        google_profile = service.userinfo().get().execute()

        google_id = google_profile["id"]
        email = google_profile["email"]
        full_name = google_profile.get("name", "")
        avatar_url = google_profile.get("picture")

        # Find or create user
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            # Try by email
            result = await self.db.execute(
                select(User).where(User.email == email, User.is_deleted.is_(False))
            )
            user = result.scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                full_name=full_name,
                avatar_url=avatar_url,
                google_id=google_id,
                is_active=True,
                is_verified=True,
            )
            self.db.add(user)
            await self.db.flush()
            # Create profile
            profile = Profile(user_id=user.id)
            self.db.add(profile)
        else:
            user.google_id = google_id
            user.google_tokens = {
                "token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "scopes": list(credentials.scopes or []),
            }
            user.last_login_at = datetime.now(timezone.utc)
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            self.db.add(user)

        await self.db.commit()
        await self.db.refresh(user)
        return user, await self.create_tokens(user)

    def _build_oauth_flow(self) -> Flow:
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        return Flow.from_client_config(
            client_config,
            scopes=GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

    # ── Password reset ────────────────────────────────────────────────────────

    async def initiate_password_reset(self, email: str) -> None:
        """Send password reset email if user exists (silent if not)."""
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()
        if user is None:
            logger.info("Password reset requested for unknown email", email=email)
            return

        token = self._create_password_reset_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        # In production, send via email service. Logged here for development.
        logger.info(
            "Password reset token generated",
            user_id=str(user.id),
            reset_url=reset_url,
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        """Validate reset token and update password."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            if payload.get("type") != "password_reset":
                raise ValueError("Not a password reset token")
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, ValueError, KeyError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            ) from exc

        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_deleted.is_(False))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        user.hashed_password = get_password_hash(new_password)
        self.db.add(user)
        await self.db.commit()
        logger.info("Password reset completed", user_id=str(user_id))

    def _create_password_reset_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=2)
        return jwt.encode(
            {"sub": str(user.id), "type": "password_reset", "exp": expire},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
