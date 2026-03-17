"""
Gmail API client with OAuth2 support.
"""
from __future__ import annotations

import base64
import email as email_lib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = structlog.get_logger(__name__)


class GmailClient:
    """Async-friendly Gmail API wrapper using google-api-python-client."""

    def __init__(self, token_dict: Dict[str, Any]) -> None:
        """
        Initialize with stored Google OAuth tokens.

        Args:
            token_dict: Dict with keys: token, refresh_token, token_uri, scopes
        """
        self._credentials = Credentials(
            token=token_dict.get("token"),
            refresh_token=token_dict.get("refresh_token"),
            token_uri=token_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=None,
            client_secret=None,
        )
        self._service = None

    def _get_service(self):
        if self._service is None:
            self._service = build("gmail", "v1", credentials=self._credentials)
        return self._service

    async def list_threads(
        self,
        max_results: int = 100,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List Gmail threads matching the query.

        Returns list of {id, snippet} dicts.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self._list_threads_sync,
            max_results,
            query,
            label_ids,
        )

    def _list_threads_sync(
        self,
        max_results: int,
        query: Optional[str],
        label_ids: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        service = self._get_service()
        kwargs: Dict[str, Any] = {
            "userId": "me",
            "maxResults": min(max_results, 500),
        }
        if query:
            kwargs["q"] = query
        if label_ids:
            kwargs["labelIds"] = label_ids

        try:
            result = service.users().threads().list(**kwargs).execute()
            return result.get("threads", [])
        except HttpError as exc:
            logger.error("Gmail list_threads failed", error=str(exc))
            return []

    async def get_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a thread and return parsed metadata."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._get_thread_sync, thread_id)

    def _get_thread_sync(self, thread_id: str) -> Optional[Dict[str, Any]]:
        service = self._get_service()
        try:
            thread = service.users().threads().get(
                userId="me", id=thread_id, format="full"
            ).execute()
        except HttpError as exc:
            logger.error("Gmail get_thread failed", thread_id=thread_id, error=str(exc))
            return None

        messages = thread.get("messages", [])
        if not messages:
            return None

        # Parse first and last message
        first_msg = messages[0]
        last_msg = messages[-1]

        subject = self._get_header(last_msg, "Subject")
        participants = list({
            self._get_header(m, "From")
            for m in messages
            if self._get_header(m, "From")
        })

        last_date_str = self._get_header(last_msg, "Date")
        last_message_at = None
        if last_date_str:
            from email.utils import parsedate_to_datetime
            try:
                last_message_at = parsedate_to_datetime(last_date_str)
            except Exception:
                pass

        body = self._extract_body(last_msg)

        return {
            "thread_id": thread_id,
            "subject": subject,
            "participants": participants,
            "message_count": len(messages),
            "last_message_at": last_message_at,
            "body": body,
            "messages": [
                {
                    "message_id": m["id"],
                    "subject": self._get_header(m, "Subject"),
                    "sender_email": self._get_header(m, "From"),
                    "received_at": self._parse_date(self._get_header(m, "Date")),
                    "body": self._extract_body(m),
                }
                for m in messages
            ],
        }

    def _get_header(self, message: Dict, name: str) -> Optional[str]:
        headers = message.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name", "").lower() == name.lower():
                return h.get("value")
        return None

    def _extract_body(self, message: Dict) -> str:
        """Extract plain text body from a Gmail message."""
        payload = message.get("payload", {})
        return self._extract_part(payload)

    def _extract_part(self, part: Dict) -> str:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        if "parts" in part:
            for subpart in part["parts"]:
                text = self._extract_part(subpart)
                if text:
                    return text
        return ""

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        from email.utils import parsedate_to_datetime
        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return None
