"""Implementation phase engine."""

import logging
from typing import Callable

from src.discovery.agent_registry import AgentRegistry
from src.protocol.a2a_client import A2AClient

logger = logging.getLogger(__name__)


class ImplementationPhase:
    """Implementation phase - executes the plan by calling agents."""
    
    def __init__(
        self,
        llm_client: Callable,
        prompt_loader: Callable,
        a2a_client: A2AClient
    ):
        """Initialize implementation phase.
        
        Args:
            llm_client: Function to call LLM
            prompt_loader: Function to load implementation prompt
            a2a_client: A2A client for agent communication
        """
        self.llm_client = llm_client
        self.prompt_loader = prompt_loader
        self.a2a_client = a2a_client
    
    def execute(
        self,
        execution_plan: str,
        agent_registry: AgentRegistry
    ) -> str:
        """Execute implementation phase.
        
        Args:
            execution_plan: Output from planning phase
            agent_registry: Registry of available agents
            
        Returns:
            Implementation results text
        """
        logger.info("⚙️  Implementation Phase: Executing plan...")
        
        # Load system prompt
        system_prompt = self.prompt_loader()
        
        # Build user message with plan and agents
        user_message = self._build_user_message(execution_plan, agent_registry)
        
        # Get LLM response with implementation instructions
        implementation_output = self.llm_client(user_message, system_prompt)
        
        # TODO: Parse the implementation output to extract agent calls
        # TODO: Execute agent calls via A2A protocol
        # TODO: Aggregate results
        
        logger.info("⚙️  Implementation Phase: Execution complete")
        logger.debug(f"Implementation output: {implementation_output[:200]}...")
        
        return implementation_output
    
    def _build_user_message(
        self,
        execution_plan: str,
        agent_registry: AgentRegistry
    ) -> str:
        """Build user message for implementation phase.
        
        Args:
            execution_plan: Planning phase output
            agent_registry: Agent registry
            
        Returns:
            Formatted user message
        """
        sections = []
        
        sections.append("## Execution Plan")
        sections.append(execution_plan)
        sections.append("")
        
        sections.append("## Available Agents")
        sections.append(agent_registry.to_prompt())
        sections.append("")
        
        sections.append("## Task")
        sections.append("Execute the plan by calling the specified agents in sequence.")
        sections.append("For each step:")
        sections.append("1. Identify the agent to call")
        sections.append("2. Prepare the message to send")
        sections.append("3. Call the agent via A2A protocol")
        sections.append("4. Collect the response")
        sections.append("5. Use the response in subsequent steps")
        sections.append("")
        sections.append("Provide a summary of the implementation results.")
        
        return "\n".join(sections)
