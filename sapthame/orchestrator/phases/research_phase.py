"""Research phase engine."""

from sapthame.discovery.agent_registry import AgentRegistry
from sapthame.phases.base_phase import BasePhase


class ResearchPhase(BasePhase):
    """Research phase - internal reasoning only, no agent calls."""
    
    def get_phase_name(self) -> str:
        """Get the name of this phase."""
        return "Research Phase"
    
    def get_emoji(self) -> str:
        """Get the emoji for this phase."""
        return "🔍"
    
    def get_start_message(self) -> str:
        """Get the start message for this phase."""
        return "Analyzing query and available agents"
    
    def get_complete_message(self) -> str:
        """Get the completion message for this phase."""
        return "Analysis complete"
    
    def _build_user_message(
        self,
        query: str,
        agent_registry: AgentRegistry
    ) -> str:
        """Build user message for research phase.
        
        Args:
            query: User query
            agent_registry: Agent registry
            
        Returns:
            Formatted user message
        """
        task_content = "\n".join([
            "Analyze the user query and available agents. Provide a research summary that:",
            "1. Breaks down what the query is asking for",
            "2. Identifies which agent capabilities are relevant",
            "3. Recommends a high-level approach",
            "4. Notes any potential challenges or requirements"
        ])
        
        return self._build_sections(
            ("User Query", query),
            ("Available Agents", agent_registry.to_prompt()),
            ("Task", task_content)
        )
