"""Saptami Orchestrator for multi-agent coordination."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.utils.llm_client import get_llm_response
from src.orchestrator.saptami_state import SaptamiState
from src.discovery.agent_registry import AgentRegistry
from src.protocol.a2a_client import A2AClient
from src.execution.phase_executor import PhaseExecutor
from src.phases.research_phase import ResearchPhase
from src.phases.planning_phase import PlanningPhase
from src.phases.implementation_phase import ImplementationPhase
from src.utils.prompt_loader import (
    load_research_prompt,
    load_planning_prompt,
    load_implementation_prompt
)

logger = logging.getLogger(__name__)


class SaptamiOrchestrator:
    """Main orchestrator coordinating research, planning, and implementation phases."""
    
    @staticmethod
    def name() -> str:
        return "SaptamiOrchestrator"
    
    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        """Initialize Saptami orchestrator.
        
        Args:
            model: LLM model to use
            temperature: Temperature for LLM
            api_key: API key for LLM
            api_base: API base URL for LLM
        """
        # Store LLM configuration
        self.model = model or "claude-3-5-sonnet-20241022"
        self.temperature = temperature or 0.0
        self.api_key = api_key
        self.api_base = api_base
        
        logger.info(f"SaptamiOrchestrator initialized with model={self.model}")
        
        # These will be initialized in setup()
        self.agent_registry = None
        self.a2a_client = None
        self.phase_executor = None
        self.state = None
        
        # Track messages for token counting
        self.orchestrator_messages = []
    
    def setup(self, agent_urls: List[str], logging_dir: Optional[Path] = None):
        """Setup the orchestrator with agent endpoints.
        
        Args:
            agent_urls: List of agent get-info.json URLs
            logging_dir: Optional directory for logging
        """
        logger.info("=" * 60)
        logger.info("SAPTAMI SETUP - Starting")
        logger.info("=" * 60)
        
        # Initialize A2A client
        self.a2a_client = A2AClient()
        
        # Initialize agent registry and discover agents
        self.agent_registry = AgentRegistry(self.a2a_client)
        logger.info(f"Discovering {len(agent_urls)} agent(s)...")
        self.agent_registry.discover_agents(agent_urls)
        logger.info(f"✓ Discovered {len(self.agent_registry.agents)} agent(s)")
        
        # Log agent details
        logger.info("\n" + self.agent_registry.view_all_agents())
        
        # Initialize phases
        research_phase = ResearchPhase(
            llm_client=self._get_llm_response,
            prompt_loader=load_research_prompt
        )
        
        planning_phase = PlanningPhase(
            llm_client=self._get_llm_response,
            prompt_loader=load_planning_prompt
        )
        
        implementation_phase = ImplementationPhase(
            llm_client=self._get_llm_response,
            prompt_loader=load_implementation_prompt,
            a2a_client=self.a2a_client
        )
        
        # Initialize phase executor
        self.phase_executor = PhaseExecutor(
            research_phase=research_phase,
            planning_phase=planning_phase,
            implementation_phase=implementation_phase
        )
        
        # Initialize state
        self.state = SaptamiState(
            agent_registry=self.agent_registry
        )
        
        logger.info("=" * 60)
        logger.info("SAPTAMI SETUP - Complete")
        logger.info("=" * 60 + "\n")
    
    def execute(self, query: str) -> Dict[str, Any]:
        """Execute the query through all phases.
        
        Args:
            query: User query to execute
            
        Returns:
            Execution result dictionary
        """
        logger.info("\n" + "=" * 60)
        logger.info("SAPTAMI EXECUTION - Starting")
        logger.info("=" * 60)
        logger.info(f"Query: {query}\n")
        
        # Execute phases
        result = self.phase_executor.execute(
            query=query,
            agent_registry=self.agent_registry,
            state=self.state
        )
        
        logger.info("=" * 60)
        logger.info(f"SAPTAMI EXECUTION - {'Complete' if result.success else 'Failed'}")
        logger.info("=" * 60)
        
        if not result.success:
            logger.error(f"Error: {result.error}")
        
        return {
            'success': result.success,
            'summary': result.summary,
            'research_output': result.research_output,
            'plan_output': result.plan_output,
            'implementation_output': result.implementation_output,
            'error': result.error,
            'state': self.state.to_dict()
        }
    
    def _get_llm_response(self, user_message: str, system_message: str) -> str:
        """Get LLM response (following current project pattern).
        
        Args:
            user_message: User message
            system_message: System message
            
        Returns:
            LLM response text
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # Track messages for token counting
        if not self.orchestrator_messages:
            self.orchestrator_messages.append({"role": "system", "content": system_message})
        self.orchestrator_messages.append({"role": "user", "content": user_message})
        
        # Call centralized LLM client
        response = get_llm_response(
            messages=messages,
            model=self.model,
            temperature=self.temperature,
            max_tokens=4096,
            api_key=self.api_key,
            api_base=self.api_base
        )
        
        # Track assistant response
        self.orchestrator_messages.append({"role": "assistant", "content": response})
        
        return response
