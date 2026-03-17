"""
Job matching LangGraph workflow.

State graph:
  analyze_requirements → compute_embedding_similarity → evaluate_skills → score_and_explain
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.prompts import JOB_MATCH_PROMPT_V1
from app.agents.schemas import JobMatchOutput

logger = structlog.get_logger(__name__)


# ── State ─────────────────────────────────────────────────────────────────────


class JobMatchState(TypedDict, total=False):
    # Inputs
    job_title: str
    company: str
    job_description: str
    requirements: List[str]
    job_seniority: Optional[str]
    employment_type: Optional[str]
    location: Optional[str]
    # Profile
    skills: List[str]
    seniority_level: Optional[str]
    years_of_experience: Optional[int]
    target_roles: List[str]
    remote_preference: Optional[str]
    # Intermediate
    parsed_requirements: Optional[List[str]]
    embedding_similarity: Optional[float]
    skill_analysis: Optional[Dict[str, Any]]
    # Output
    output: Optional[JobMatchOutput]
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────


def analyze_requirements(state: JobMatchState) -> JobMatchState:
    """Parse and normalize job requirements."""
    requirements = state.get("requirements") or []
    description = state.get("job_description") or ""

    # Extract bullet points from description as supplemental requirements
    extra = [
        line.strip().lstrip("•-*").strip()
        for line in description.split("\n")
        if line.strip().startswith(("•", "-", "*")) and len(line.strip()) > 10
    ]
    all_reqs = list(dict.fromkeys(requirements + extra[:20]))  # deduplicate
    state["parsed_requirements"] = all_reqs
    return state


def compute_embedding_similarity(state: JobMatchState) -> JobMatchState:
    """
    Compute embedding similarity between job and profile.
    Currently returns a heuristic based on skill overlap.
    Future: use actual vector embeddings.
    """
    skills = set(s.lower() for s in (state.get("skills") or []))
    requirements = state.get("parsed_requirements") or []
    req_text = " ".join(requirements).lower()

    # Simple keyword overlap as proxy for embedding similarity
    matches = sum(1 for skill in skills if skill in req_text)
    similarity = min(1.0, matches / max(len(skills), 1) * 1.5) if skills else 0.3
    state["embedding_similarity"] = round(similarity, 3)
    return state


async def evaluate_skills(state: JobMatchState) -> JobMatchState:
    """Use LLM to perform deep skill gap analysis."""
    agent = BaseAgent()
    prompt = JOB_MATCH_PROMPT_V1.format(
        skills=", ".join(state.get("skills") or []),
        seniority_level=state.get("seniority_level") or "unknown",
        years_of_experience=state.get("years_of_experience") or "unknown",
        target_roles=", ".join(state.get("target_roles") or []),
        remote_preference=state.get("remote_preference") or "flexible",
        job_title=state.get("job_title", ""),
        company=state.get("company", ""),
        location=state.get("location") or "unspecified",
        job_seniority=state.get("job_seniority") or "unspecified",
        employment_type=state.get("employment_type") or "unspecified",
        job_description=(state.get("job_description") or "")[:3000],
        requirements="\n".join(state.get("parsed_requirements") or [])[:1000],
    )
    try:
        data = await agent.invoke_json(prompt)
        state["skill_analysis"] = data
    except Exception as exc:
        logger.warning("evaluate_skills LLM failed, using heuristic", error=str(exc))
        skills_set = set(s.lower() for s in (state.get("skills") or []))
        req_text = " ".join(state.get("parsed_requirements") or []).lower()
        skill_matches = [s for s in skills_set if s in req_text]
        state["skill_analysis"] = {
            "match_score": state.get("embedding_similarity", 0.5),
            "skill_matches": skill_matches,
            "skill_gaps": [],
            "strengths": [],
            "weaknesses": [],
            "explanation": "Match computed via keyword overlap.",
        }
    return state


def score_and_explain(state: JobMatchState) -> JobMatchState:
    """Combine scores and produce final JobMatchOutput."""
    analysis = state.get("skill_analysis") or {}
    embedding_sim = state.get("embedding_similarity", 0.5)

    llm_score = float(analysis.get("match_score", embedding_sim))
    # Blend LLM score and embedding similarity
    final_score = round(0.7 * llm_score + 0.3 * embedding_sim, 3)
    final_score = max(0.0, min(1.0, final_score))

    state["output"] = JobMatchOutput(
        match_score=final_score,
        skill_matches=analysis.get("skill_matches") or [],
        skill_gaps=analysis.get("skill_gaps") or [],
        strengths=analysis.get("strengths") or [],
        weaknesses=analysis.get("weaknesses") or [],
        explanation=analysis.get("explanation") or "",
        model_used=BaseAgent().model_name,
        prompt_version="v1",
    )
    return state


# ── Graph ─────────────────────────────────────────────────────────────────────


def build_job_matching_graph() -> StateGraph:
    graph = StateGraph(JobMatchState)
    graph.add_node("analyze_requirements", analyze_requirements)
    graph.add_node("compute_embedding_similarity", compute_embedding_similarity)
    graph.add_node("evaluate_skills", evaluate_skills)
    graph.add_node("score_and_explain", score_and_explain)

    graph.set_entry_point("analyze_requirements")
    graph.add_edge("analyze_requirements", "compute_embedding_similarity")
    graph.add_edge("compute_embedding_similarity", "evaluate_skills")
    graph.add_edge("evaluate_skills", "score_and_explain")
    graph.add_edge("score_and_explain", END)
    return graph


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_job_matching_graph().compile()
    return _compiled_graph


async def run_job_matching_workflow(job, profile) -> JobMatchOutput:
    """
    Entry point: run the full job-matching workflow.

    Args:
        job: Job ORM instance
        profile: Profile ORM instance

    Returns:
        JobMatchOutput with match score and analysis
    """
    initial_state: JobMatchState = {
        "job_title": job.title,
        "company": job.company_name,
        "job_description": job.cleaned_description or job.raw_description or "",
        "requirements": list(job.requirements or []),
        "job_seniority": job.seniority,
        "employment_type": job.employment_type,
        "location": job.location,
        "skills": list(profile.skills or []),
        "seniority_level": profile.seniority_level,
        "years_of_experience": profile.years_of_experience,
        "target_roles": list(profile.target_roles or []),
        "remote_preference": profile.remote_preference,
    }

    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("output") or JobMatchOutput(
        match_score=0.0, explanation="Workflow returned no output"
    )
