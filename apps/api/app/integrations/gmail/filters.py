"""
Recruiting-related email detection filters.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

# Keywords that strongly indicate recruiting-related emails
RECRUITING_KEYWORDS = [
    "interview",
    "application",
    "applied",
    "recruiter",
    "recruiting",
    "job offer",
    "offer letter",
    "assessment",
    "coding challenge",
    "technical screen",
    "onsite",
    "hiring",
    "career opportunity",
    "position",
    "role at",
    "joining us",
    "background check",
    "onboarding",
    "rejection",
    "unfortunately",
    "moving forward",
    "next steps",
    "schedule",
    "availability",
    "linkedin",
    "glassdoor",
    "indeed",
    "lever",
    "greenhouse",
    "workday",
    "taleo",
]

# Domains that suggest recruiting emails
RECRUITING_DOMAINS = [
    "linkedin.com",
    "glassdoor.com",
    "indeed.com",
    "lever.co",
    "greenhouse.io",
    "workday.com",
    "taleo.net",
    "jobvite.com",
    "smartrecruiters.com",
    "icims.com",
    "brassring.com",
    "myworkdayjobs.com",
]


def is_recruiting_related(thread_data: Dict[str, Any]) -> bool:
    """
    Return True if the email thread appears to be job-search related.

    Checks subject line, body, and sender domain.
    """
    subject = (thread_data.get("subject") or "").lower()
    body = (thread_data.get("body") or "").lower()[:2000]
    participants = [p.lower() for p in (thread_data.get("participants") or [])]

    # Check sender domain
    for participant in participants:
        if any(domain in participant for domain in RECRUITING_DOMAINS):
            return True

    # Check subject and body for keywords
    combined_text = f"{subject} {body}"
    keyword_hits = sum(1 for kw in RECRUITING_KEYWORDS if kw in combined_text)
    return keyword_hits >= 1


def classify_recruiting_signal(text: str) -> List[str]:
    """
    Return a list of matched recruiting signal keywords in the text.
    Useful for pre-filtering before LLM classification.
    """
    lower = text.lower()
    return [kw for kw in RECRUITING_KEYWORDS if kw in lower]


def extract_email_domain(email: str) -> str:
    """Extract domain from email address."""
    if "@" in email:
        return email.split("@", 1)[1].lower().strip()
    return ""
