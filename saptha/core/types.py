"""
Core types and schemas for the distributed agent orchestrator.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task in the orchestration system."""
    PENDING = "pending"
    ROUTING = "routing"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentCapability(str, Enum):
    """Capabilities that agents can provide."""
    WEB_SEARCH = "web_search"
    KNOWLEDGE_BASE = "knowledge_base"
    DATA_ANALYSIS = "data_analysis"
    CODE_GENERATION = "code_generation"
    TEXT_PROCESSING = "text_processing"
    IMAGE_PROCESSING = "image_processing"
    REASONING = "reasoning"


class ExecutionMode(str, Enum):
    """How agents should be executed for a task."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    COLLABORATIVE = "collaborative"


class Message(BaseModel):
    """A message in the conversation."""
    id: UUID = Field(default_factory=uuid.uuid4)
    content: str
    role: str = "user"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentInfo(BaseModel):
    """Information about an available agent."""
    id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    endpoint: str
    is_available: bool = True
    last_health_check: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskRequest(BaseModel):
    """A request to execute a task."""
    id: UUID = Field(default_factory=uuid.uuid4)
    message: Message
    context_id: Optional[str] = None
    required_capabilities: List[AgentCapability] = Field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    max_agents: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Response from an agent."""
    agent_id: str
    task_id: UUID
    content: str
    success: bool = True
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Result of a completed task."""
    task_id: UUID
    status: TaskStatus
    final_response: Optional[str] = None
    agent_responses: List[AgentResponse] = Field(default_factory=list)
    execution_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Context for a conversation."""
    id: str
    messages: List[Message] = Field(default_factory=list)
    active_task_ids: List[UUID] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
