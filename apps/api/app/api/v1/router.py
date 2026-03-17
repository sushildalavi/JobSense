"""
API v1 main router — aggregates all sub-routers.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routers.agents import router as agents_router
from app.api.v1.routers.analytics import router as analytics_router
from app.api.v1.routers.applications import router as applications_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.calendar import router as calendar_router
from app.api.v1.routers.emails import router as emails_router
from app.api.v1.routers.jobs import router as jobs_router
from app.api.v1.routers.profile import router as profile_router
from app.api.v1.routers.resumes import router as resumes_router
from app.api.v1.routers.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(profile_router)
api_router.include_router(resumes_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(emails_router)
api_router.include_router(calendar_router)
api_router.include_router(analytics_router)
api_router.include_router(agents_router)
