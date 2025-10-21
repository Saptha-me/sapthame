# |---------------------------------------------------------------|
# |                                                               |
# |                  Give Feedback / Get Help                     |
# |    https://github.com/Saptha-me/sapthame/issues/new/choose    |
# |                                                               |
# |---------------------------------------------------------------|
#
#  Thank you users! We ❤️ you! - 🌻

"""
Conductor for multi-agent coordination and turn-based execution.

The Conductor orchestrates complex tasks by coordinating multiple specialized agents
through a turn-based execution model. It manages conversation history, state tracking,
and action execution across research, planning, and implementation phases.

Architecture:
    - Turn-based execution: Each turn consists of LLM output → action parsing → execution
    - State management: Tracks phase progress, outputs, and execution status
    - Agent coordination: Discovers and delegates work to specialized agents
    - Context management: Maintains conversation history, scratchpad, and todo list

Example Usage:
    ```python
    from sapthame.orchestrator import Conductor
    
    # Initialize conductor
    conductor = Conductor(
        model="claude-sonnet-4-5-20250929",
        temperature=0.0
    )
    
    # Setup with agent endpoints
    conductor.setup(
        agent_urls=[
            "http://localhost:8001/market-intel-agent.get-info.json",
            "http://localhost:8002/traction-metrics-agent.get-info.json"
        ]
    )
    
    # Run research stage
    result = conductor.run_research_stage(
        client_question="What is the market opportunity for AI coding assistants?",
        max_turns=20
    )
    
    # Access results
    print(f"Completed: {result['completed']}")
    print(f"Findings: {result['finish_message']}")
    print(f"Scratchpad: {result['scratchpad']}")
    ```

Key Components:
    - State: Tracks phase progress and outputs
    - ConversationHistory: Maintains turn-based interaction history
    - ScratchpadManager: Temporary working memory for findings
    - TodoManager: Task tracking with completion status
    - TurnExecutor: Executes actions from LLM output
    - ActionHandler: Handles agent queries and state mutations
"""

from __future__ import annotations as _annotations

from pathlib import Path
from typing import Optional, Dict, Any, List

from sapthame.utils.llm_client import get_llm_response
from sapthame.settings import app_settings
from sapthame.discovery.agent_registry import AgentRegistry
from sapthame.protocol.bindu_client import BinduClient
from sapthame.utils.prompt_loader import load_prompt_from_file

from .state_managers.state import State
from .state_managers.conversation_history import ConversationHistory
from .turn import Turn

from .turn.turn_executor import TurnExecutor
from .actions.parser import ActionParser
from .actions.handler import ActionHandler
from .state_managers.scratchpad import ScratchpadManager
from .state_managers.todo import TodoManager

from sapthame.utils.logging import get_logger


logger = get_logger("sapthame.orchestrator.conductor")

class Conductor:
    """Main conductor coordinating research, planning, and implementation phases."""
    
    def __init__(
        self,
        prompt_path: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs
    ):
        """Initialize Conductor.
        
        Args:
            prompt_path: Path to system message file
            model: LLM model to use
            temperature: Temperature for LLM
            api_key: API key for LLM
            api_base: API base URL for LLM
        """
        # Store LLM configuration
        self.prompt_path = prompt_path
        self.model = model or "claude-sonnet-4-5-20250929"
        self.temperature = temperature or 0.0
        self.api_key = api_key
        self.api_base = api_base
        
        logger.info(f"Conductor initialized with model={self.model}")
        
        # These will be initialized in setup()
        self.agent_registry = None
        self.bindu_client = None
        self.phase_executor = None
        self.state = None
        
        # Track messages for token counting
        self.conductor_messages = []

        self.conversation_history = None
        self.action_parser = None
        self.action_handler = None
        self.executor = None
        self.scratchpad_manager = None
        self.todo_manager = None

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

        # Initialize state managers
        self.scratchpad_manager = ScratchpadManager()
        self.todo_manager = TodoManager()
        self.conversation_history = ConversationHistory(
            max_turns=app_settings.orchestrator.max_conversation_turns
        )
        self.state = State(
            agent_registry=self.agent_registry,
            conversation_history=self.conversation_history
        )

        
        # Initialize agent registry and discover agents
        self.agent_registry = AgentRegistry(
            
        )
        logger.info(f"Discovering {len(agent_urls)} agent(s)...")
        self.agent_registry.discover_agents(agent_urls)
        logger.info(f"✓ Discovered {len(self.agent_registry.agents)} agent(s)")
        
        # Log agent details
        logger.info("\n" + self.agent_registry.view_all_agents())

        # Initialize action components
        self.action_parser = ActionParser()
        self.action_handler = ActionHandler(
            agent_registry=self.agent_registry,
            scratchpad_manager=self.scratchpad_manager,
            todo_manager=self.todo_manager
        )
        
        # Initialize turn executor
        self.executor = TurnExecutor(
            action_parser=self.action_parser,
            action_handler=self.action_handler
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
        llm_response = self._get_llm_response(user_message, self.system_message)

        result = self.executor.execute(llm_response)

        turn = Turn(
            llm_output=llm_response,
            actions_executed=result.actions_executed,
            env_responses=result.env_responses,
            subagent_trajectories=result.agent_trajectories
        )

        self.conversation_history.add_turn(turn)
        turn_data = {
                "instruction": instruction,
                "user_message": user_message,
                "llm_response": llm_response,
                "actions_executed": [str(action) for action in result.actions_executed],
                "env_responses": result.env_responses,
                "subagent_trajectories": result.agent_trajectories,
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
    
    def run_research_stage(
        self,
        client_question: str,
        max_turns: int = 20
    ) -> Dict[str, Any]:
        """Run research stage with turn-based execution.
        
        Args:
            client_question: The research question
            max_turns: Maximum number of turns
            
        Returns:
            Research stage result
        """
        logger.info("\n" + "=" * 60)
        logger.info("🔍 RESEARCH STAGE - Starting")
        logger.info("=" * 60)
        logger.info(f"Question: {client_question}\n")
        
        turns_executed = 0
        self.state.current_phase = "research"
        self.state.done = False
        
        while not self.state.done and turns_executed < max_turns:
            turns_executed += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Research Turn {turns_executed}/{max_turns}")
            logger.info(f"{'='*60}")
            
            try:
                # Build user message with current state
                user_message = self._build_research_prompt(
                    client_question=client_question,
                    scratchpad=self.scratchpad_manager.to_prompt(),
                    todo=self.todo_manager.to_prompt(),
                    conversation_history=self.conversation_history.to_prompt()
                )
                
                # Get LLM response
                llm_response = self._get_llm_response(user_message, self.system_message)
                
                # Execute turn
                result = self.executor.execute(llm_response)
                
                # Create turn for history
                turn = Turn(
                    llm_output=llm_response,
                    actions_executed=result.actions_executed,
                    env_responses=result.env_responses,
                    subagent_trajectories=result.agent_trajectories
                )
                
                # Add to conversation history
                self.conversation_history.add_turn(turn)
                
                # Log turn if logger available
                if self.turn_logger:
                    turn_data = {
                        "client_question": client_question,
                        "user_message": user_message,
                        "llm_response": llm_response,
                        "actions_executed": [str(action) for action in result.actions_executed],
                        "env_responses": result.env_responses,
                        "agent_trajectories": result.agent_trajectories,
                        "done": result.done,
                        "finish_message": result.finish_message,
                        "has_error": result.has_error,
                        "scratchpad": self.scratchpad_manager.get_content(),
                        "todo": self.todo_manager.get_status()
                    }
                    self.turn_logger.log_turn(turns_executed, turn_data)
                
                # Check if done
                if result.done:
                    self.state.done = True
                    self.state.finish_message = result.finish_message
                    self.state.research_output = result.finish_message
                    logger.info(f"✓ Research stage complete: {result.finish_message}")
                    break
                    
            except Exception as e:
                logger.error(f"Error in turn {turns_executed}: {e}", exc_info=True)
        
        logger.info("\n" + "=" * 60)
        logger.info(f"RESEARCH STAGE - {'Complete' if self.state.done else 'Max turns reached'}")
        logger.info("=" * 60)
        
        return {
            'completed': self.state.done,
            'finish_message': self.state.finish_message,
            'turns_executed': turns_executed,
            'scratchpad': self.scratchpad_manager.get_content(),
            'todo': self.todo_manager.get_status(),
            'max_turns_reached': turns_executed >= max_turns
        }
    
    def _load_research_system_message(self) -> str:
        """Load research stage system message with agent information."""
        # Load base research prompt
        if self.base_system_message:
            base_prompt = self.base_system_message
        else:
            # Load default turn-based research prompt
            prompt_path = Path(__file__).parent.parent / "system_msgs" / "research_turn_based_prompt.md"
            with open(prompt_path, 'r', encoding='utf-8') as f:
                base_prompt = f.read()
        
        # Build agent list section
        agent_list = self._build_agent_list()
        
        # Inject agent list into prompt (replace placeholder or append)
        if "{AGENT_LIST_HERE}" in base_prompt:
            return base_prompt.replace("{AGENT_LIST_HERE}", agent_list)
        else:
            # Append agent list if no placeholder found
            return base_prompt + f"\n\n## Available Agents\n\n{agent_list}"
    
    def _build_agent_list(self) -> str:
        """Build formatted list of available agents."""
        if not self.agent_registry or not self.agent_registry.agents:
            return "(No agents available)"
        
        lines = []
        for agent_id, agent in self.agent_registry.agents.items():
            lines.append(f"### {agent.name} (`{agent_id}`)")
            lines.append(f"**Description**: {agent.description}")
            
            if agent.skills:
                lines.append("**Skills**:")
                for skill in agent.skills:
                    lines.append(f"- {skill.name}: {skill.description}")
            
            lines.append("")  # Empty line between agents
        
        return "\n".join(lines)
    
    def _build_research_prompt(
        self,
        client_question: str,
        scratchpad: str,
        todo: str,
        conversation_history: str
    ) -> str:
        """Build research stage prompt."""
        return f"""## Research Task
{client_question}

{scratchpad}

{todo}

## Conversation History
{conversation_history}

## Instructions
Use the available actions to research this question thoroughly. Query research agents, organize findings in the scratchpad, track remaining questions in the todo list. When you have sufficient information, use the finish_stage action to complete the research.
"""
        
    
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
