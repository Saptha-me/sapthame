# |---------------------------------------------------------------|
# |                                                               |
# |                  Give Feedback / Get Help                     |
# |    https://github.com/Saptha-me/sapthame/issues/new/choose    |
# |                                                               |
# |---------------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""Conductor for multi-agent coordination."""

from pathlib import Path
from typing import Optional, Dict, Any, List

from sapthame.utils.llm_client import get_llm_response
from sapthame.orchestrator.state import State
from sapthame.orchestrator.conversation_history import ConversationHistory
from sapthame.discovery.agent_registry import AgentRegistry
from sapthame.protocol.a2a_client import A2AClient
from sapthame.execution.phase_executor import PhaseExecutor
from sapthame.phases.research_phase import ResearchPhase
from sapthame.phases.planning_phase import PlanningPhase
from sapthame.phases.implementation_phase import ImplementationPhase
from sapthame.utils.prompt_loader import (
    load_prompt_from_file,
    load_research_prompt,
    load_planning_prompt,
    load_implementation_prompt
)

from sapthame.utils.logging import get_logger

# Configure logging for the module
logger = get_logger("sapthame.orchestrator.conductor")

class Conductor:
    """Main conductor coordinating research, planning, and implementation phases."""
    
    @staticmethod
    def name() -> str:
        return "SapthaConductor"
    
    def __init__(
        self,
        system_message_path: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        """Initialize Conductor.
        
        Args:
            system_message_path: Path to system message file
            model: LLM model to use
            temperature: Temperature for LLM
            api_key: API key for LLM
            api_base: API base URL for LLM
        """
        # Store LLM configuration
        self.system_message_path = system_message_path
        self.model = model or "claude-sonnet-4-5-20250929"
        self.temperature = temperature or 0.0
        self.api_key = api_key
        self.api_base = api_base
        
        logger.info(f"Conductor initialized with model={self.model}")

        self.system_message = load_prompt_from_file(system_message_path)
        
        # These will be initialized in setup()
        self.agent_registry = None
        self.a2a_client = None
        self.phase_executor = None
        self.state = None
        
        # Track messages for token counting
        self.conductor_messages = []

        self.conversation_history = None
        self.action_parser = None
        self.action_handler = None

        self.turn_logger = None
        self.logging_dir = None
    
    def setup(self, agent_urls: List[str], logging_dir: Optional[Path] = None):
        """Setup the conductor with agent endpoints.
        
        Args:
            agent_urls: List of agent get-info.json URLs
            logging_dir: Optional directory for logging
        """
        logger.info("=" * 60)
        logger.info("🌻 Sapthame Conductor - Starting")
        logger.info("=" * 60)

        self.conversation_history = ConversationHistory()
        
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
        self.state = State(
            agent_registry=self.agent_registry,
            conversation_history=self.conversation_history,
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

    def run(self, instruction: str, max_turns: int = 50) -> Dict[str, Any]:
        """Run the orchestrator until completion or max turns.
        
        Args:
            instruction: The main task to complete
            max_turns: Maximum number of turns before stopping
            
        Returns:
            Final execution summary
        """
        turns_executed = 0
        
        while not self.state.done and turns_executed < max_turns:
            turns_executed += 1
            logger.info(f"Executing turn {turns_executed}")
            logging.info(f"\n{'='*60}")
            logging.info(f"ORCHESTRATOR MAIN LOOP - Turn {turns_executed}/{max_turns}")
            logging.info(f"{'='*60}")
            
            try:
                result = self.execute_turn(instruction, turns_executed)
                
                if result['done']:
                    logger.info(f"Task completed: {result['finish_message']}")
                    break
                    
            except Exception as e:
                logger.error(f"Error in turn {turns_executed}: {e}")
                # Could add error to conversation history here
                
        return {
            'completed': self.state.done,
            'finish_message': self.state.finish_message,
            'turns_executed': turns_executed,
            'max_turns_reached': turns_executed >= max_turns
        }

    def execute_turn(self, instruction: str, turn_num: int) -> Dict[str, Any]:
        user_message = f"## Current Task\n{instruction}\n\n{self.state.to_prompt()}"
        llm_response = self._get_llm_response(user_message)

        result = self.executor.execute(llm_response)

        turn = Turn(
            llm_output=llm_response,
            actions_executed=result.actions_executed,
            env_responses=result.env_responses,
            subagent_trajectories=result.subagent_trajectories
        )

        self.conversation_history.add_turn(turn)
        turn_data = {
                "instruction": instruction,
                "user_message": user_message,
                "llm_response": llm_response,
                "actions_executed": [str(action) for action in result.actions_executed],
                "env_responses": result.env_responses,
                "subagent_trajectories": result.subagent_trajectories,
                "done": result.done,
                "finish_message": result.finish_message,
                "has_error": result.has_error,
                "state_snapshot": self.state.to_dict()
            }
        self.turn_logger.log_turn(turn_num, turn_data)

        if result.done:
            self.state.done = True
            self.state.finish_message = result.finish_message
            logger.info(f"🟡 ORCHESTRATOR: Task marked as DONE - {result.finish_message}")
        else:
            logger.info(f"🟡 ORCHESTRATOR TURN {turn_num} COMPLETE - Continuing...\n")

        return {
            'done': result.done,
            'finish_message': result.finish_message,
            'has_error': result.has_error,
            'actions_executed': len(result.actions_executed),
            'turn': turn
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
        if not self.conductor_messages:
            self.conductor_messages.append({"role": "system", "content": system_message})
        self.conductor_messages.append({"role": "user", "content": user_message})
        
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
        self.conductor_messages.append({"role": "assistant", "content": response})
        
        return response
