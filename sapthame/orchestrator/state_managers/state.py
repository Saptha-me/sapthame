"""State management for Saptami orchestrator."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from sapthame.discovery.agent_registry import AgentRegistry
from sapthame.orchestrator.conversation_history import ConversationHistory


@dataclass
class State:
    """Orchestrator state tracking execution progress."""
    
    agent_registry: AgentRegistry
    conversation_history: ConversationHistory
    
    # Query
    query: Optional[str] = None
    
    # Phase tracking
    current_phase: str = "research"
    research_output: Optional[str] = None
    plan_output: Optional[str] = None
    implementation_output: Optional[str] = None
    
    # Execution state
    done: bool = False
    finish_message: Optional[str] = None
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary.
        
        Returns:
            Dictionary representation of state
        """
        return {
            "current_phase": self.current_phase,
            "research_output": self.research_output,
            "plan_output": self.plan_output,
            "implementation_output": self.implementation_output,
            "done": self.done,
            "finish_message": self.finish_message,
            "metadata": self.metadata,
            "agents": [agent.to_dict() for agent in self.agent_registry.agents.values()],
        }
    
    def to_prompt(self) -> str:
        """Generate prompt representation of current state.
        
        Returns:
            Formatted string for LLM context
        """
        sections = []
        
        sections.append(f"## Current Phase: {self.current_phase}")
        
        if self.research_output:
            sections.append(f"## Research Output\n{self.research_output}")
        
        if self.plan_output:
            sections.append(f"## Plan Output\n{self.plan_output}")
        
        if self.implementation_output:
            sections.append(f"## Implementation Output\n{self.implementation_output}")
        
        if self.metadata:
            sections.append(f"## Metadata\n{self.metadata}")
        
        return "\n\n".join(sections)
