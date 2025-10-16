"""Research phase engine."""

import logging
from typing import Callable

from src.discovery.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


class ResearchPhase:
    """Research phase - internal reasoning only, no agent calls."""
    
    def __init__(
        self,
        llm_client: Callable,
        prompt_loader: Callable
    ):
        """Initialize research phase.
        
        Args:
            llm_client: Function to call LLM
            prompt_loader: Function to load research prompt
        """
        self.llm_client = llm_client
        self.prompt_loader = prompt_loader
    
    def execute(
        self,
        query: str,
        agent_registry: AgentRegistry
    ) -> str:
        """Execute research phase.
        
        Args:
            query: User query
            agent_registry: Registry of available agents
            
        Returns:
            Research summary text
        """
        logger.info("🔍 Research Phase: Analyzing query and available agents...")
        
        # Load system prompt
        system_prompt = self.prompt_loader()
        
        # Build user message with query and agent capabilities
        user_message = self._build_user_message(query, agent_registry)
        
        # Get LLM response
        research_summary = self.llm_client(user_message, system_prompt)
        
        logger.info("🔍 Research Phase: Analysis complete")
        logger.debug(f"Research summary: {research_summary[:200]}...")
        
        return research_summary
    
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
        sections = []
        
        sections.append("## User Query")
        sections.append(query)
        sections.append("")
        
        sections.append("## Available Agents")
        sections.append(agent_registry.to_prompt())
        sections.append("")
        
        sections.append("## Task")
        sections.append("Analyze the user query and available agents. Provide a research summary that:")
        sections.append("1. Breaks down what the query is asking for")
        sections.append("2. Identifies which agent capabilities are relevant")
        sections.append("3. Recommends a high-level approach")
        sections.append("4. Notes any potential challenges or requirements")
        
        return "\n".join(sections)
