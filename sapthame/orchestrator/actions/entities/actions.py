"""Action entities for turn-based execution."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


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
    """Update the scratchpad with findings."""
    content: str
    operation: str = "append"  # append, replace, clear
    
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
    """Update the todo list."""
    item: str
    operation: str = "add"  # add, complete, remove
    index: Optional[int] = None  # For complete/remove operations
    
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
    """Mark the current stage as complete."""
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
