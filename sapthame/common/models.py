"""Common data models for Sapthame.

This module contains all shared data models used across the Sapthame system,
organized into logical sections:

1. Agent Models: Skill, AgentInfo
2. Execution Models: PhaseResult, ExecutionContext, Phase
3. Action Models: Base Action class and concrete action types
4. State Models: TodoItem
"""

from __future__ import annotations as _annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Literal


__all__ = [
    # Agent Models
    "Skill",
    "AgentInfo",
    # Execution Models
    "PhaseResult",
    "ExecutionContext",
    "ExecutionResult",
    "Phase",
    # Action Models
    "Action",
    "QueryAgentAction",
    "UpdateScratchpadAction",
    "UpdateTodoAction",
    "FinishStageAction",
    # State Models
    "TodoItem",
]


# ============================================================================
# Agent Models
# ============================================================================

@dataclass
class Skill:
    """Agent skill definition.
    
    Represents a capability that an agent can perform.
    """
    name: str
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create Skill from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description
        }


@dataclass
class AgentInfo:
    """Agent information from get-info.json.
    
    Complete metadata about a discovered agent including its capabilities,
    skills, and protocol version.
    """
    id: str
    name: str
    description: str
    url: str
    version: str
    protocol_version: str
    skills: List[Skill]
    capabilities: Dict[str, Any]
    extra_data: Dict[str, Any]
    agent_trust: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInfo":
        """Create AgentInfo from dictionary."""
        skills = [Skill.from_dict(s) for s in data.get("skills", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            url=data["url"],
            version=data["version"],
            protocol_version=data.get("protocolVersion", "1.0"),
            skills=skills,
            capabilities=data.get("capabilities", {}),
            extra_data=data.get("extraData", {}),
            agent_trust=data.get("agentTrust", "medium")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "protocolVersion": self.protocol_version,
            "skills": [s.to_dict() for s in self.skills],
            "capabilities": self.capabilities,
            "extraData": self.extra_data,
            "agentTrust": self.agent_trust
        }
    
    def get_skill_names(self) -> List[str]:
        """Get list of skill names."""
        return [skill.name for skill in self.skills]


# ============================================================================
# Execution Models
# ============================================================================

@dataclass
class PhaseResult:
    """Result of executing a phase.
    
    Contains success status, outputs, and any errors from phase execution.
    """
    success: bool
    summary: str
    research_output: Optional[str] = None
    plan_output: Optional[str] = None
    implementation_output: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert phase result to dictionary format."""
        return {
            "success": self.success,
            "summary": self.summary,
            "research_output": self.research_output,
            "plan_output": self.plan_output,
            "implementation_output": self.implementation_output,
            "error": self.error
        }


@dataclass
class ExecutionContext:
    """Context passed between phases during execution.
    
    Maintains state and results as execution progresses through phases.
    """
    
    query: str
    research_summary: Optional[str] = None
    execution_plan: Optional[str] = None
    implementation_results: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "research_summary": self.research_summary,
            "execution_plan": self.execution_plan,
            "implementation_results": self.implementation_results,
            "metadata": self.metadata
        }


@dataclass
class ExecutionResult:
    """Result of executing a single turn.
    
    Contains all actions executed, environment responses, error status,
    and completion information from a turn execution.
    """
    actions_executed: List[Action] = field(default_factory=list)
    env_responses: List[str] = field(default_factory=list)
    has_error: bool = False
    finish_message: Optional[str] = None
    done: bool = False
    agent_trajectories: Optional[Dict[str, Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution result to dictionary format.
        
        Returns:
            Dictionary representation of execution result.
        """
        return {
            "actions_executed": [action.to_dict() for action in self.actions_executed],
            "env_responses": self.env_responses,
            "has_error": self.has_error,
            "finish_message": self.finish_message,
            "done": self.done,
            "agent_trajectories": self.agent_trajectories
        }


class Phase(str, Enum):
    """Valid execution phases.
    
    Defines the three main phases of task execution.
    """
    RESEARCH = "research"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"


# ============================================================================
# Action Models
# ============================================================================

@dataclass
class Action(ABC):
    """Base class for all actions."""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        """String representation for logging."""
        pass


@dataclass
class QueryAgentAction(Action):
    """Query a research agent via Bindu protocol."""
    agent_id: str
    query: str
    context_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "query_agent",
            "agent_id": self.agent_id,
            "query": self.query,
            "context_id": self.context_id
        }
    
    def __str__(self) -> str:
        query_preview = self.query[:50] + "..." if len(self.query) > 50 else self.query
        return f"QueryAgent({self.agent_id}, query='{query_preview}')"


@dataclass
class UpdateScratchpadAction(Action):
    """Update the scratchpad with findings.
    
    Supports append, replace, and clear operations.
    """
    content: str
    operation: Literal["append", "replace", "clear"] = "append"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "update_scratchpad",
            "content": self.content,
            "operation": self.operation
        }
    
    def __str__(self) -> str:
        return f"UpdateScratchpad(operation={self.operation})"


@dataclass
class UpdateTodoAction(Action):
    """Update the todo list.
    
    Supports add, complete, and remove operations.
    """
    item: str
    operation: Literal["add", "complete", "remove"] = "add"
    index: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "update_todo",
            "item": self.item,
            "operation": self.operation,
            "index": self.index
        }
    
    def __str__(self) -> str:
        item_preview = self.item[:30] + "..." if len(self.item) > 30 else self.item
        return f"UpdateTodo(operation={self.operation}, item='{item_preview}')"


@dataclass
class FinishStageAction(Action):
    """Mark the current stage as complete.
    
    Signals completion of a phase with a summary message.
    """
    message: str
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "finish_stage",
            "message": self.message,
            "summary": self.summary
        }
    
    def __str__(self) -> str:
        return f"FinishStage(message='{self.message}')"


# ============================================================================
# State Models
# ============================================================================

@dataclass
class TodoItem:
    """Represents a single todo item.
    
    Tracks task text and completion status.
    """
    text: str
    completed: bool = False
    
    def __str__(self) -> str:
        """String representation of todo item."""
        status = "✓" if self.completed else "○"
        return f"{status} {self.text}"


