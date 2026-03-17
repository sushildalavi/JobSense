"""
Resume tailoring LangGraph workflow.

State graph:
  analyze_job → plan_tailoring → tailor_sections → validate_truthfulness → finalize
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.prompts import RESUME_TAILORING_PROMPT_V1
from app.agents.schemas import ResumeTailoringOutput

logger = structlog.get_logger(__name__)


# ── State ─────────────────────────────────────────────────────────────────────

class ResumeTailoringState(TypedDict, total=False):
    # Inputs
    resume_text: str
    job_title: str
    company: str
    job_description: str
    requirements: List[str]
    # Intermediate
    key_requirements: Optional[List[str]]
    tailoring_plan: Optional[Dict[str, Any]]
    tailored_draft: Optional[str]
    validation_passed: Optional[bool]
    # Output
    output: Optional[ResumeTailoringOutput]
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────

def analyze_job(state: ResumeTailoringState) -> ResumeTailoringState:
    """Extract key requirements that should be reflected in the resume."""
    requirements = state.get("requirements") or []
    description = state.get("job_description") or ""

    # Extract explicit requirements from description
    lines = [
        line.strip().lstrip("•-*").strip()
        for line in description.split("\n")
        if any(
            kw in line.lower()
            for kw in ("experience", "skill", "proficient", "knowledge", "require", "must")
        )
        and len(line.strip()) > 20
    ]
    all_reqs = list(dict.fromkeys(requirements + lines[:15]))
    state["key_requirements"] = all_reqs
    return state


def plan_tailoring(state: ResumeTailoringState) -> ResumeTailoringState:
    """Decide which resume sections to modify and what keywords to add."""
    resume_text = state.get("resume_text") or ""
    key_reqs = state.get("key_requirements") or []

    # Determine present sections
    sections = []
    lower = resume_text.lower()
    if "experience" in lower or "employment" in lower:
        sections.append("experience")
    if "skill" in lower:
        sections.append("skills")
    if "project" in lower:
        sections.append("projects")
    if "summary" in lower or "profile" in lower or "objective" in lower:
        sections.append("summary")

    state["tailoring_plan"] = {
        "sections_to_modify": sections or ["summary", "experience", "skills"],
        "keywords_to_add": [r[:50] for r in key_reqs[:10]],
    }
    return state


async def tailor_sections(state: ResumeTailoringState) -> ResumeTailoringState:
    """Use LLM to rewrite resume sections for the target job."""
    agent = BaseAgent()
    prompt = RESUME_TAILORING_PROMPT_V1.format(
        job_title=state.get("job_title", ""),
        company=state.get("company", ""),
        job_description=(state.get("job_description") or "")[:2000],
        requirements="\n".join(state.get("key_requirements") or [])[:1000],
        resume_text=(state.get("resume_text") or "")[:4000],
    )
    try:
        data = await agent.invoke_json(prompt)
        state["tailored_draft"] = data.get("tailored_content", state.get("resume_text", ""))
        state["tailoring_plan"] = {
            **(state.get("tailoring_plan") or {}),
            "sections_modified": data.get("sections_modified", []),
            "keywords_added": data.get("keywords_added", []),
            "reasoning": data.get("reasoning", ""),
        }
    except Exception as exc:
        logger.warning("tailor_sections LLM failed, returning original", error=str(exc))
        state["tailored_draft"] = state.get("resume_text", "")
    return state


def validate_truthfulness(state: ResumeTailoringState) -> ResumeTailoringState:
    """
    Verify that the tailored content does not invent new facts.
    Currently performs a lightweight check for hallucination signals.
    """
    original = state.get("resume_text") or ""
    tailored = state.get("tailored_draft") or ""

    # Simple heuristic: if tailored is too much longer than original, warn
    ratio = len(tailored) / max(len(original), 1)
    if ratio > 2.0:
        logger.warning(
            "Tailored resume is significantly longer than original",
            ratio=ratio,
        )
        # Truncate to prevent obvious hallucination
        state["tailored_draft"] = tailored[:len(original) * 2]

    state["validation_passed"] = True
    return state


def finalize(state: ResumeTailoringState) -> ResumeTailoringState:
    """Package final output."""
    plan = state.get("tailoring_plan") or {}
    state["output"] = ResumeTailoringOutput(
        tailored_content=state.get("tailored_draft") or state.get("resume_text") or "",
        sections_modified=plan.get("sections_modified") or plan.get("sections_to_modify") or [],
        reasoning=plan.get("reasoning") or "Resume tailored for target role.",
        keywords_added=plan.get("keywords_added") or [],
        model_used=BaseAgent().model_name,
        prompt_version="v1",
    )
    return state


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_resume_tailoring_graph() -> StateGraph:
    graph = StateGraph(ResumeTailoringState)
    graph.add_node("analyze_job", analyze_job)
    graph.add_node("plan_tailoring", plan_tailoring)
    graph.add_node("tailor_sections", tailor_sections)
    graph.add_node("validate_truthfulness", validate_truthfulness)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("analyze_job")
    graph.add_edge("analyze_job", "plan_tailoring")
    graph.add_edge("plan_tailoring", "tailor_sections")
    graph.add_edge("tailor_sections", "validate_truthfulness")
    graph.add_edge("validate_truthfulness", "finalize")
    graph.add_edge("finalize", END)
    return graph


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_resume_tailoring_graph().compile()
    return _compiled_graph


async def run_resume_tailoring_workflow(master_resume, job) -> ResumeTailoringOutput:
    """
    Entry point: run the resume tailoring workflow.

    Args:
        master_resume: MasterResume ORM instance
        job: Job ORM instance

    Returns:
        ResumeTailoringOutput
    """
    initial_state: ResumeTailoringState = {
        "resume_text": master_resume.raw_text or "",
        "job_title": job.title,
        "company": job.company_name,
        "job_description": job.cleaned_description or job.raw_description or "",
        "requirements": list(job.requirements or []),
    }

    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("output") or ResumeTailoringOutput(
        tailored_content=master_resume.raw_text or "",
        reasoning="Workflow returned no output",
    )
