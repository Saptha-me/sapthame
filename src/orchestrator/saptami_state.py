"""State management for Saptami orchestrator."""

from typing import Optional
from src.discovery.agent_registry import AgentRegistry


class SaptamiState:
    """Manages the complete state for Saptami orchestrator."""
    
    def __init__(self, agent_registry: AgentRegistry):
        """Initialize Saptami state.
        
        Args:
            agent_registry: Registry of discovered agents
        """
        self.agent_registry = agent_registry
        self.query: Optional[str] = None
        self.current_phase: str = "init"
        self.research_summary: Optional[str] = None
        self.execution_plan: Optional[str] = None
        self.implementation_results: Optional[str] = None
        self.done: bool = False
    
    def to_dict(self) -> dict:
        """Convert state to dictionary format.
        
        Returns:
            State as dictionary
        """
        return {
            "query": self.query,
            "current_phase": self.current_phase,
            "research_summary": self.research_summary,
            "execution_plan": self.execution_plan,
            "implementation_results": self.implementation_results,
            "done": self.done,
            "agents": [agent.to_dict() for agent in self.agent_registry.get_all_agents()]
        }
    
    def to_prompt(self) -> str:
        """Convert state to prompt format for LLM.
        
        Returns:
            Formatted state for LLM prompt
        """
        sections = []
        
        sections.append("## Current State\n")
        sections.append(f"Phase: {self.current_phase}")
        
        if self.research_summary:
            sections.append("\n## Research Summary\n")
            sections.append(self.research_summary)
        
        if self.execution_plan:
            sections.append("\n## Execution Plan\n")
            sections.append(self.execution_plan)
        
        if self.implementation_results:
            sections.append("\n## Implementation Results\n")
            sections.append(self.implementation_results)
        
        return "\n".join(sections)
