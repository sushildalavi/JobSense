"""
Models package — imports all ORM models to ensure they are registered with SQLAlchemy Base.
"""

from app.models.agent import AgentRun, AutomationSession
from app.models.application import Application, ApplicationEvent
from app.models.calendar import CalendarEvent
from app.models.document import Document
from app.models.email import EmailThread, ParsedEmail
from app.models.job import Job, JobClusterMember, JobDedupCluster, JobMatch, JobSource
from app.models.profile import Profile
from app.models.resume import MasterResume, ResumeVersion
from app.models.user import User

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
