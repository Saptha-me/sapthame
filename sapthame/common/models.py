

@dataclass
class ExecutionResult:
    """Result of executing a single LLM response."""
    actions_executed: List[Action]
    env_responses: List[str]  # Only responses that should be shown in history
    has_error: bool
    finish_message: Optional[str] = None
    done: bool = False  # True if FinishAction was executed
    subagent_trajectories: Optional[Dict[str, Dict[str, Any]]] = None
    
    def to_dict(self) -> dict:
        """Convert execution result to dictionary format."""
        result = {
            "actions_executed": [action.to_dict() for action in self.actions_executed],
            "env_responses": self.env_responses,
            "has_error": self.has_error,
            "finish_message": self.finish_message,
            "done": self.done
        }
        if self.subagent_trajectories:
            result["subagent_trajectories"] = self.subagent_trajectories
        return result