"""
Pydantic v2 schemas — barrel export.
"""

from app.schemas.agent import AgentRunCreate, AgentRunResponse, WorkflowTriggerRequest
from app.schemas.analytics import (
    AnalyticsSummary,
    DashboardStats,
    FunnelStage,
    ScoreBucket,
    SourceStat,
    WeeklyStat,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationEventResponse,
    ApplicationListItem,
    ApplicationNoteCreate,
    ApplicationNoteResponse,
    ApplicationResponse,
    ApplicationUpdate,
    StatusTransitionRequest,
)
from app.schemas.auth import (
    GoogleOAuthCallback,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.schemas.email import (
    EmailClassificationResponse,
    EmailSyncRequest,
    EmailThreadResponse,
    ParsedEmailResponse,
)
from app.schemas.job import (
    JobFilter,
    JobListItem,
    JobMatchResponse,
    JobRankingResponse,
    JobResponse,
    JobSearchRequest,
    JobSourceResponse,
)
from app.schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from app.schemas.resume import (
    MasterResumeCreate,
    MasterResumeResponse,
    MasterResumeUpdate,
    ParsedResumeData,
    ResumeVersionCreate,
    ResumeVersionResponse,
    TailoringRequest,
    TailoringResponse,
)
from app.schemas.user import UserBase, UserCreate, UserProfile, UserResponse, UserUpdate

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "GoogleOAuthCallback",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfile",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileResponse",
    "MasterResumeCreate",
    "MasterResumeUpdate",
    "MasterResumeResponse",
    "ResumeVersionCreate",
    "ResumeVersionResponse",
    "ParsedResumeData",
    "TailoringRequest",
    "TailoringResponse",
    "JobResponse",
    "JobListItem",
    "JobFilter",
    "JobMatchResponse",
    "JobSourceResponse",
    "JobSearchRequest",
    "JobRankingResponse",
    "ApplicationCreate",
    "ApplicationUpdate",
    "ApplicationResponse",
    "ApplicationListItem",
    "ApplicationEventResponse",
    "StatusTransitionRequest",
    "ApplicationNoteCreate",
    "ApplicationNoteResponse",
    "EmailThreadResponse",
    "ParsedEmailResponse",
    "EmailSyncRequest",
    "EmailClassificationResponse",
    "CalendarEventResponse",
    "CalendarEventCreate",
    "CalendarEventUpdate",
    "DashboardStats",
    "FunnelStage",
    "WeeklyStat",
    "SourceStat",
    "ScoreBucket",
    "AnalyticsSummary",
    "AgentRunResponse",
    "AgentRunCreate",
    "WorkflowTriggerRequest",
]
