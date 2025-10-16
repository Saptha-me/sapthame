"""Planning phase engine."""

import logging
from typing import Callable

from src.discovery.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


class PlanningPhase:
    """Planning phase - creates execution sequence based on research."""
    
    def __init__(
        self,
        llm_client: Callable,
        prompt_loader: Callable
    ):
        """Initialize planning phase.
        
        Args:
            llm_client: Function to call LLM
            prompt_loader: Function to load planning prompt
        """
        self.llm_client = llm_client
        self.prompt_loader = prompt_loader
    
    def execute(
        self,
        research_summary: str,
        agent_registry: AgentRegistry
    ) -> str:
        """Execute planning phase.
        
        Args:
            research_summary: Output from research phase
            agent_registry: Registry of available agents
            
        Returns:
            Execution plan text
        """
        logger.info("📋 Planning Phase: Creating execution sequence...")
        
        # Load system prompt
        system_prompt = self.prompt_loader()
        
        # Build user message with research summary and agents
        user_message = self._build_user_message(research_summary, agent_registry)
        
        # Get LLM response
        execution_plan = self.llm_client(user_message, system_prompt)
        
        logger.info("📋 Planning Phase: Plan created")
        logger.debug(f"Execution plan: {execution_plan[:200]}...")
        
        return execution_plan
    
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
        sections = []
        
        sections.append("## Research Summary")
        sections.append(research_summary)
        sections.append("")
        
        sections.append("## Available Agents")
        sections.append(agent_registry.to_prompt())
        sections.append("")
        
        sections.append("## Task")
        sections.append("Based on the research summary, create a step-by-step execution plan that:")
        sections.append("1. Lists each step in sequence")
        sections.append("2. Specifies which agent to use for each step")
        sections.append("3. Describes what to ask each agent")
        sections.append("4. Explains the expected output from each step")
        sections.append("5. Shows how steps build on each other")
        
        return "\n".join(sections)
