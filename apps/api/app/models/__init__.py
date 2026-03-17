"""
Models package — imports all ORM models to ensure they are registered with SQLAlchemy Base.
"""
from app.models.user import User
from app.models.profile import Profile
from app.models.resume import MasterResume, ResumeVersion
from app.models.job import Job, JobSource, JobMatch, JobDedupCluster, JobClusterMember
from app.models.application import Application, ApplicationEvent
from app.models.email import EmailThread, ParsedEmail
from app.models.calendar import CalendarEvent
from app.models.agent import AgentRun, AutomationSession
from app.models.document import Document

__all__ = [
    "User",
    "Profile",
    "MasterResume",
    "ResumeVersion",
    "Job",
    "JobSource",
    "JobMatch",
    "JobDedupCluster",
    "JobClusterMember",
    "Application",
    "ApplicationEvent",
    "EmailThread",
    "ParsedEmail",
    "CalendarEvent",
    "AgentRun",
    "AutomationSession",
    "Document",
]
