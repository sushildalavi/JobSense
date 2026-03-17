"""
Apify API client — runs actors and retrieves results.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

APIFY_BASE_URL = "https://api.apify.com/v2"


class ApifyClient:
    """Async Apify API client."""

    def __init__(self, api_token: Optional[str] = None) -> None:
        self.api_token = api_token or settings.APIFY_API_TOKEN
        self._headers = {"Authorization": f"Bearer {self.api_token}"}

    async def run_actor(
        self,
        actor_id: str,
        input_data: Dict[str, Any],
        timeout_secs: int = 300,
    ) -> List[Dict[str, Any]]:
        """
        Run an Apify actor synchronously and return the dataset items.

        Args:
            actor_id: The Apify actor ID (e.g. "apify/linkedin-jobs-scraper")
            input_data: Actor input parameters
            timeout_secs: Max wait time in seconds

        Returns:
            List of raw job record dicts from the dataset
        """
        async with httpx.AsyncClient(timeout=timeout_secs + 30) as client:
            # Start the run
            run_response = await client.post(
                f"{APIFY_BASE_URL}/acts/{actor_id}/runs",
                headers=self._headers,
                json={"input": input_data},
                params={"timeout": timeout_secs},
            )
            run_response.raise_for_status()
            run_data = run_response.json().get("data", {})
            run_id = run_data.get("id")

            if not run_id:
                raise ValueError(f"Apify run did not return a run ID for actor {actor_id}")

            logger.info("Apify actor run started", actor_id=actor_id, run_id=run_id)

            # Poll for completion
            completed = await self._wait_for_run(client, run_id, timeout_secs)
            if not completed:
                raise TimeoutError(f"Apify run {run_id} timed out after {timeout_secs}s")

            # Fetch dataset
            dataset_id = run_data.get("defaultDatasetId")
            if not dataset_id:
                # Re-fetch run details to get dataset ID
                run_detail = await client.get(
                    f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                    headers=self._headers,
                )
                run_detail.raise_for_status()
                dataset_id = run_detail.json().get("data", {}).get("defaultDatasetId")

            items = await self._fetch_dataset(client, dataset_id)
            logger.info(
                "Apify actor run completed",
                actor_id=actor_id,
                run_id=run_id,
                items=len(items),
            )
            return items

    async def _wait_for_run(
        self,
        client: httpx.AsyncClient,
        run_id: str,
        timeout_secs: int,
    ) -> bool:
        """Poll run status until SUCCEEDED or timeout."""
        elapsed = 0
        poll_interval = 5
        terminal_states = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}

        while elapsed < timeout_secs:
            response = await client.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                headers=self._headers,
            )
            response.raise_for_status()
            status = response.json().get("data", {}).get("status", "")

            if status in terminal_states:
                return status == "SUCCEEDED"

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        return False

    async def _fetch_dataset(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch all items from an Apify dataset."""
        response = await client.get(
            f"{APIFY_BASE_URL}/datasets/{dataset_id}/items",
            headers=self._headers,
            params={"limit": limit, "format": "json"},
        )
        response.raise_for_status()
        return response.json() or []

    async def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get current status of an actor run."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{APIFY_BASE_URL}/actor-runs/{run_id}",
                headers=self._headers,
            )
            response.raise_for_status()
            return response.json().get("data", {})
