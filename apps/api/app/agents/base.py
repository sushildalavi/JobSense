"""
BaseAgent — shared utilities for all LangGraph workflows.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional, TypeVar

import structlog
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.llm import get_llm

logger = structlog.get_logger(__name__)
T = TypeVar("T")


class BaseAgent:
    """
    Base class providing logging, LLM access, retry logic,
    and JSON parsing helpers for all agent workflows.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.llm: BaseChatModel = get_llm(provider, model)
        self.model_name: str = getattr(self.llm, "model_name", model or "unknown")
        self._log = structlog.get_logger(self.__class__.__name__)

    async def invoke(self, prompt: str) -> str:
        """
        Call the LLM and return the raw string response.
        Logs latency and token usage.
        """
        start = time.monotonic()
        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)
            elapsed = time.monotonic() - start
            self._log.debug(
                "LLM invoked",
                model=self.model_name,
                elapsed_ms=round(elapsed * 1000),
                chars=len(content),
            )
            return content
        except Exception as exc:
            elapsed = time.monotonic() - start
            self._log.error(
                "LLM invocation failed",
                model=self.model_name,
                elapsed_ms=round(elapsed * 1000),
                error=str(exc),
            )
            raise

    def parse_json(self, raw: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM response, stripping markdown code fences.
        Raises ValueError on failure.
        """
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```", 2)
            if len(parts) >= 2:
                cleaned = parts[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            self._log.error("JSON parse failed", raw=raw[:200], error=str(exc))
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

    async def invoke_json(self, prompt: str) -> Dict[str, Any]:
        """Invoke LLM and parse response as JSON."""
        raw = await self.invoke(prompt)
        return self.parse_json(raw)
