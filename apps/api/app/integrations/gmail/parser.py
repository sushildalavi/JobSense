"""
Gmail email parser — extracts structured data from thread payloads.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def parse_thread(thread_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a raw Gmail thread dict (as returned by GmailClient.get_thread)
    into a normalized structure.

    Returns:
        dict with keys: subject, participants, message_count,
                        last_message_at, body, messages
    """
    subject = _clean_subject(thread_data.get("subject") or "")
    participants = thread_data.get("participants") or []
    message_count = thread_data.get("message_count", 1)
    last_message_at = thread_data.get("last_message_at")
    body = thread_data.get("body") or ""
    messages = thread_data.get("messages") or []

    return {
        "subject": subject,
        "participants": _normalize_email_list(participants),
        "message_count": message_count,
        "last_message_at": last_message_at,
        "body": body,
        "messages": [_parse_message(m) for m in messages],
    }


def _parse_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    sender_raw = msg.get("sender_email") or ""
    sender_email, sender_name = _parse_email_address(sender_raw)
    return {
        "message_id": msg.get("message_id"),
        "subject": _clean_subject(msg.get("subject") or ""),
        "sender_email": sender_email,
        "sender_name": sender_name,
        "received_at": msg.get("received_at"),
        "body": msg.get("body") or "",
    }


def _clean_subject(subject: str) -> str:
    """Remove Re:/Fwd: prefixes and normalize whitespace."""
    cleaned = re.sub(r"^(re:|fwd?:|fw:)\s*", "", subject, flags=re.IGNORECASE)
    return cleaned.strip()


def _parse_email_address(raw: str) -> tuple[Optional[str], Optional[str]]:
    """Parse 'Name <email@domain.com>' format."""
    if not raw:
        return None, None
    match = re.match(r'^"?([^"<]+)"?\s*<([^>]+)>', raw)
    if match:
        name = match.group(1).strip().strip('"')
        email = match.group(2).strip().lower()
        return email, name
    # Plain email address
    email = raw.strip().lower()
    if "@" in email:
        return email, None
    return None, None


def _normalize_email_list(participants: List[str]) -> List[str]:
    """Normalize a list of raw email address strings."""
    result = []
    for p in participants:
        email, _ = _parse_email_address(p)
        if email:
            result.append(email)
    return list(dict.fromkeys(result))  # deduplicate preserving order
