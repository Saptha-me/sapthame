"""Implementation phase engine."""

import logging
from typing import Callable

from src.discovery.agent_registry import AgentRegistry
from src.protocol.a2a_client import A2AClient
from sapthame.phases.base_phase import BasePhase

logger = logging.getLogger(__name__)


class ImplementationPhase(BasePhase):
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
            a2a_client: A2A protocol client
        """
        super().__init__(llm_client, prompt_loader)
        self.a2a_client = a2a_client
    
    def get_phase_name(self) -> str:
        """Get the name of this phase."""
        return "Implementation Phase"
    
    def get_emoji(self) -> str:
        """Get the emoji for this phase."""
        return "⚙️"
    
    def get_start_message(self) -> str:
        """Get the start message for this phase."""
        return "Executing plan"
    
    def get_complete_message(self) -> str:
        """Get the completion message for this phase."""
        return "Execution complete"
    
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
        # Call parent execute which handles the LLM interaction
        implementation_output = super().execute(execution_plan, agent_registry)
        
        # TODO: Parse the implementation output to extract agent calls
        # TODO: Execute agent calls via A2A protocol
        # TODO: Aggregate results
        
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
        task_content = "\n".join([
            "Execute the plan by calling the specified agents in sequence.",
            "For each step:",
            "1. Identify the agent to call",
            "2. Prepare the message to send",
            "3. Call the agent via A2A protocol",
            "4. Collect the response",
            "5. Use the response in subsequent steps",
            "",
            "Provide a summary of the implementation results."
        ])
        
        return self._build_sections(
            ("Execution Plan", execution_plan),
            ("Available Agents", agent_registry.to_prompt()),
            ("Task", task_content)
        )
