"""
Email classification LangGraph workflow.

State graph:
  preprocess → classify → extract_entities → link_to_application → update_status
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict

import structlog
from langgraph.graph import END, StateGraph

from app.agents.base import BaseAgent
from app.agents.prompts import EMAIL_CLASSIFICATION_PROMPT_V1, EMAIL_ENTITY_EXTRACTION_PROMPT_V1
from app.agents.schemas import EmailClassificationOutput, EmailEntityExtractionOutput
from app.models.email import EmailClassification

logger = structlog.get_logger(__name__)


# ── State ─────────────────────────────────────────────────────────────────────


class EmailClassificationState(TypedDict, total=False):
    # Inputs
    subject: str
    body: str
    sender: str
    thread_id: Optional[str]
    # Intermediate
    cleaned_text: Optional[str]
    classification_data: Optional[Dict[str, Any]]
    entity_data: Optional[Dict[str, Any]]
    # Outputs
    classification_output: Optional[EmailClassificationOutput]
    entity_output: Optional[EmailEntityExtractionOutput]
    error: Optional[str]


# ── Nodes ─────────────────────────────────────────────────────────────────────


def preprocess(state: EmailClassificationState) -> EmailClassificationState:
    """Clean and truncate email content for LLM processing."""
    subject = state.get("subject") or ""
    body = state.get("body") or ""

    # Strip HTML tags naively
    import re

    cleaned_body = re.sub(r"<[^>]+>", " ", body)
    cleaned_body = re.sub(r"\s+", " ", cleaned_body).strip()

    state["cleaned_text"] = f"Subject: {subject}\n\n{cleaned_body[:2000]}"
    return state


async def classify(state: EmailClassificationState) -> EmailClassificationState:
    """Call LLM to classify the email thread."""
    agent = BaseAgent()
    prompt = EMAIL_CLASSIFICATION_PROMPT_V1.format(
        subject=state.get("subject") or "",
        body=state.get("cleaned_text") or "",
        sender=state.get("sender") or "",
    )
    try:
        data = await agent.invoke_json(prompt)
        state["classification_data"] = data
    except Exception as exc:
        logger.warning("Email classification LLM failed", error=str(exc))
        state["classification_data"] = {
            "classification": "unclassified",
            "confidence": 0.0,
            "reasoning": "Classification failed",
        }
    return state


async def extract_entities(state: EmailClassificationState) -> EmailClassificationState:
    """Extract structured entities from the email."""
    classification = (state.get("classification_data") or {}).get("classification", "")
    # Only extract for relevant classifications
    if classification in ("noise", "unclassified"):
        state["entity_data"] = {}
        return state

    agent = BaseAgent()
    prompt = EMAIL_ENTITY_EXTRACTION_PROMPT_V1.format(email_content=state.get("cleaned_text") or "")
    try:
        data = await agent.invoke_json(prompt)
        state["entity_data"] = data
    except Exception as exc:
        logger.warning("Entity extraction LLM failed", error=str(exc))
        state["entity_data"] = {}
    return state


def link_to_application(state: EmailClassificationState) -> EmailClassificationState:
    """Placeholder for application linking logic (handled asynchronously in tasks)."""
    return state


def update_status(state: EmailClassificationState) -> EmailClassificationState:
    """Package final outputs."""
    cls_data = state.get("classification_data") or {}
    entity_data = state.get("entity_data") or {}

    # Validate classification value
    raw_cls = cls_data.get("classification", "unclassified")
    try:
        cls_enum = EmailClassification(raw_cls)
    except ValueError:
        cls_enum = EmailClassification.unclassified

    state["classification_output"] = EmailClassificationOutput(
        classification=cls_enum.value,
        confidence=float(cls_data.get("confidence", 0.0)),
        reasoning=cls_data.get("reasoning") or "",
        model_used=BaseAgent().model_name,
    )

    # Parse datetime if present
    interview_dt = None
    raw_dt = entity_data.get("interview_datetime")
    if raw_dt:
        from dateutil import parser as date_parser

        try:
            interview_dt = date_parser.parse(raw_dt)
        except Exception:
            pass

    state["entity_output"] = EmailEntityExtractionOutput(
        company=entity_data.get("company"),
        job_title=entity_data.get("job_title"),
        interviewer=entity_data.get("interviewer"),
        interview_datetime=interview_dt,
        timezone=entity_data.get("timezone"),
        meeting_link=entity_data.get("meeting_link"),
        next_action=entity_data.get("next_action"),
    )
    return state


# ── Graph ─────────────────────────────────────────────────────────────────────


def build_email_classification_graph() -> StateGraph:
    graph = StateGraph(EmailClassificationState)
    graph.add_node("preprocess", preprocess)
    graph.add_node("classify", classify)
    graph.add_node("extract_entities", extract_entities)
    graph.add_node("link_to_application", link_to_application)
    graph.add_node("update_status", update_status)

    graph.set_entry_point("preprocess")
    graph.add_edge("preprocess", "classify")
    graph.add_edge("classify", "extract_entities")
    graph.add_edge("extract_entities", "link_to_application")
    graph.add_edge("link_to_application", "update_status")
    graph.add_edge("update_status", END)
    return graph


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_email_classification_graph().compile()
    return _compiled_graph


async def run_email_classification_workflow(
    content: str,
    subject: Optional[str] = None,
    sender: Optional[str] = None,
    thread_id: Optional[str] = None,
) -> EmailClassificationOutput:
    """
    Entry point: classify an email and return classification output.
    """
    initial_state: EmailClassificationState = {
        "subject": subject or content[:100],
        "body": content,
        "sender": sender or "",
        "thread_id": thread_id,
    }
    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("classification_output") or EmailClassificationOutput(
        classification=EmailClassification.unclassified.value,
        confidence=0.0,
        reasoning="Workflow returned no output",
    )


async def run_entity_extraction_workflow(
    content: str,
    subject: Optional[str] = None,
    sender: Optional[str] = None,
) -> EmailEntityExtractionOutput:
    """Entry point: extract entities from an email."""
    initial_state: EmailClassificationState = {
        "subject": subject or content[:100],
        "body": content,
        "sender": sender or "",
    }
    graph = _get_graph()
    final_state = await graph.ainvoke(initial_state)
    return final_state.get("entity_output") or EmailEntityExtractionOutput()
