"""
Job discovery LangGraph workflow.

State graph:
  trigger_ingestion → normalize_jobs → deduplicate → compute_matches → notify
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

import structlog
from langgraph.graph import END, StateGraph

logger = structlog.get_logger(__name__)


# ── State ─────────────────────────────────────────────────────────────────────


class JobDiscoveryState(TypedDict, total=False):
    # Inputs
    user_id: Optional[str]
    source_ids: Optional[List[str]]
    # Intermediate
    ingestion_results: Optional[List[Dict[str, Any]]]
    normalized_count: Optional[int]
    dedup_count: Optional[int]
    match_count: Optional[int]
    # Output
    summary: Optional[Dict[str, Any]]
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────


async def trigger_ingestion(state: JobDiscoveryState) -> JobDiscoveryState:
    """Trigger Apify job ingestion for configured sources."""
    from app.tasks.ingestion import sync_apify_jobs

    source_ids = state.get("source_ids")
    user_id = state.get("user_id")

    results = []
    if source_ids:
        for source_id in source_ids:
            task = sync_apify_jobs.delay(source_id, user_id)
            results.append({"source_id": source_id, "task_id": task.id})
    else:
        task = sync_apify_jobs.delay(None, user_id)
        results.append({"source_id": "all", "task_id": task.id})

    state["ingestion_results"] = results
    logger.info("Ingestion triggered", count=len(results))
    return state


async def normalize_jobs(state: JobDiscoveryState) -> JobDiscoveryState:
    """
    Normalization runs inside process_raw_job tasks.
    Here we just record the count.
    """
    state["normalized_count"] = len(state.get("ingestion_results") or [])
    return state


async def deduplicate(state: JobDiscoveryState) -> JobDiscoveryState:
    """Trigger deduplication pass."""
    from app.tasks.ingestion import run_deduplication

    run_deduplication.delay()
    state["dedup_count"] = 0  # actual count updated by dedup task
    return state


async def compute_matches(state: JobDiscoveryState) -> JobDiscoveryState:
    """Trigger match computation for the user."""
    user_id = state.get("user_id")
    if user_id:
        from app.tasks.matching import compute_job_matches_for_user

        compute_job_matches_for_user.delay(user_id)
        state["match_count"] = 1
    else:
        from app.tasks.matching import recompute_all_matches

        recompute_all_matches.delay()
        state["match_count"] = -1  # all users
    return state


def notify(state: JobDiscoveryState) -> JobDiscoveryState:
    """Package summary and optionally send notifications."""
    state["summary"] = {
        "ingestion_tasks": len(state.get("ingestion_results") or []),
        "normalized_count": state.get("normalized_count", 0),
        "dedup_triggered": True,
        "match_computation_triggered": True,
    }
    logger.info("Job discovery workflow complete", summary=state["summary"])
    return state


# ── Graph ─────────────────────────────────────────────────────────────────────


def build_job_discovery_graph() -> StateGraph:
    graph = StateGraph(JobDiscoveryState)
    graph.add_node("trigger_ingestion", trigger_ingestion)
    graph.add_node("normalize_jobs", normalize_jobs)
    graph.add_node("deduplicate", deduplicate)
    graph.add_node("compute_matches", compute_matches)
    graph.add_node("notify", notify)

    graph.set_entry_point("trigger_ingestion")
    graph.add_edge("trigger_ingestion", "normalize_jobs")
    graph.add_edge("normalize_jobs", "deduplicate")
    graph.add_edge("deduplicate", "compute_matches")
    graph.add_edge("compute_matches", "notify")
    graph.add_edge("notify", END)
    return graph


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_job_discovery_graph().compile()
    return _compiled_graph


async def run_job_discovery_workflow(
    user_id: Optional[str] = None,
    source_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Entry point: trigger the full job discovery pipeline."""
    initial_state: JobDiscoveryState = {
        "user_id": user_id,
        "source_ids": source_ids,
    }
    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("summary") or {}
