"""
Agent run Pydantic v2 schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.agent import AgentRunStatus, WorkflowName


class AgentRunCreate(BaseModel):
    workflow_name: WorkflowName
    input_data: Optional[Dict[str, Any]] = None


class WorkflowTriggerRequest(BaseModel):
    workflow_name: WorkflowName
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    async_execution: bool = True


class AgentRunResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    workflow_name: WorkflowName
    status: AgentRunStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    prompt_version: Optional[str] = None
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
