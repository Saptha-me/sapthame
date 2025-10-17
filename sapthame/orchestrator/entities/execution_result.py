"""Execution result for turn-based execution."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from sapthame.orchestrator.actions.entities.actions import Action


@dataclass
class ExecutionResult:
    """Result of executing a turn."""
    
    actions_executed: List[Action] = field(default_factory=list)
    env_responses: List[str] = field(default_factory=list)
    has_error: bool = False
    done: bool = False
    finish_message: Optional[str] = None
    agent_trajectories: Optional[Dict[str, Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "actions_executed": [action.to_dict() for action in self.actions_executed],
            "env_responses": self.env_responses,
            "has_error": self.has_error,
            "done": self.done,
            "finish_message": self.finish_message,
            "agent_trajectories": self.agent_trajectories
        }
