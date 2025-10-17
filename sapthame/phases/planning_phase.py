"""Planning phase engine."""

from sapthame.discovery.agent_registry import AgentRegistry
from sapthame.phases.base_phase import BasePhase


class PlanningPhase(BasePhase):
    """Planning phase - creates execution sequence based on research."""
    
    def get_phase_name(self) -> str:
        """Get the name of this phase."""
        return "Planning Phase"
    
    def get_emoji(self) -> str:
        """Get the emoji for this phase."""
        return "📋"
    
    def get_start_message(self) -> str:
        """Get the start message for this phase."""
        return "Creating execution sequence"
    
    def get_complete_message(self) -> str:
        """Get the completion message for this phase."""
        return "Plan created"
    
    def _build_user_message(
        self,
        research_summary: str,
        agent_registry: AgentRegistry
    ) -> str:
        """Build user message for planning phase.
        
        Args:
            research_summary: Research phase output
            agent_registry: Agent registry
            
        Returns:
            Formatted user message
        """
        task_content = "\n".join([
            "Based on the research summary, create a step-by-step execution plan that:",
            "1. Lists each step in sequence",
            "2. Specifies which agent to use for each step",
            "3. Describes what to ask each agent",
            "4. Explains the expected output from each step",
            "5. Shows how steps build on each other"
        ])
        
        return self._build_sections(
            ("Research Summary", research_summary),
            ("Available Agents", agent_registry.to_prompt()),
            ("Task", task_content)
        )
