"""Common data models for Saptami."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Skill:
    """Agent skill definition."""
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
    """Agent information from get-info.json."""
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


@dataclass
class PhaseResult:
    """Result of executing a phase."""
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
    """Context passed between phases during execution."""
    
    query: str
    research_summary: Optional[str] = None
    execution_plan: Optional[str] = None
    implementation_results: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'research_summary': self.research_summary,
            'execution_plan': self.execution_plan,
            'implementation_results': self.implementation_results,
            'metadata': self.metadata
        }



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


@dataclass
class TodoItem:
    """Represents a single todo item."""
    text: str
    completed: bool = False
    
    def __str__(self) -> str:
        """String representation of todo item."""
        status = "✓" if self.completed else "○"
        return f"{status} {self.text}"


class Phase(str, Enum):
    """Valid execution phases."""
    RESEARCH = "research"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
