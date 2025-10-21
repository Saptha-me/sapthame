"""Handler for executing actions."""

import logging
from typing import Tuple, Dict, Any

from .discovery.agent_registry import AgentRegistry
from .protocol.bindu_client import BinduClient
from .orchestrator.state_managers.scratchpad import ScratchpadManager
from .orchestrator.state_managers.todo import TodoManager
from .common.models import (
    Action,
    QueryAgentAction,
    UpdateScratchpadAction,
    UpdateTodoAction,
    FinishStageAction
)

logger = logging.getLogger(__name__)


class ActionHandler:
    """Handles execution of actions."""
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        scratchpad_manager: ScratchpadManager,
        todo_manager: TodoManager
    ):
        self.agent_registry = agent_registry
        self.scratchpad_manager = scratchpad_manager
        self.todo_manager = todo_manager
        self.agent_trajectories: Dict[str, Dict[str, Any]] = {}
    
    def handle_action(self, action: Action) -> Tuple[str, bool]:
        """Execute an action and return (output, is_error).
        
        Args:
            action: Action to execute
            
        Returns:
            Tuple of (output_message, is_error)
        """
        try:
            if isinstance(action, QueryAgentAction):
                return self._handle_query_agent(action)
            elif isinstance(action, UpdateScratchpadAction):
                return self._handle_update_scratchpad(action)
            elif isinstance(action, UpdateTodoAction):
                return self._handle_update_todo(action)
            elif isinstance(action, FinishStageAction):
                return self._handle_finish_stage(action)
            else:
                return f"Unknown action type: {type(action)}", True
                
        except Exception as e:
            logger.error(f"Error handling action {action}: {e}", exc_info=True)
            return f"Error executing action: {str(e)}", True
    
    def _handle_query_agent(self, action: QueryAgentAction) -> Tuple[str, bool]:
        """Handle QueryAgentAction."""
        logger.info(f"Querying agent {action.agent_id}: {action.query[:100]}...")
        
        # Get agent from registry
        agent = self.agent_registry.get_agent(action.agent_id)
        if not agent:
            return f"Agent '{action.agent_id}' not found in registry", True
        
        try:
            # Create Bindu client for this agent
            client = BinduClient(
                agent_url=agent.url,
                timeout=60
            )
            
            # Send message and wait for response
            task = client.send_and_wait(
                text=action.query,
                context_id=action.context_id,
                max_wait=120.0
            )
            
            # Extract response
            if task.is_completed():
                response_text = self._extract_task_response(task)
                
                # Track agent trajectory
                self.agent_trajectories[task.taskId] = {
                    "agent_id": action.agent_id,
                    "query": action.query,
                    "response": response_text,
                    "task_id": task.taskId
                }
                
                return f"Agent {action.agent_id} responded:\n{response_text}", False
            else:
                return f"Agent {action.agent_id} task did not complete: {task.state}", True
                
        except Exception as e:
            logger.error(f"Error querying agent {action.agent_id}: {e}")
            return f"Error querying agent {action.agent_id}: {str(e)}", True
    
    def _handle_update_scratchpad(self, action: UpdateScratchpadAction) -> Tuple[str, bool]:
        """Handle UpdateScratchpadAction."""
        if action.operation == "append":
            self.scratchpad_manager.append(action.content)
            return "Scratchpad updated (appended)", False
        elif action.operation == "replace":
            self.scratchpad_manager.replace(action.content)
            return "Scratchpad updated (replaced)", False
        elif action.operation == "clear":
            self.scratchpad_manager.clear()
            return "Scratchpad cleared", False
        else:
            return f"Unknown scratchpad operation: {action.operation}", True
    
    def _handle_update_todo(self, action: UpdateTodoAction) -> Tuple[str, bool]:
        """Handle UpdateTodoAction."""
        if action.operation == "add":
            self.todo_manager.add_item(action.item)
            return f"Added todo item: {action.item}", False
        elif action.operation == "complete":
            if action.index is not None:
                self.todo_manager.complete_item(action.index)
                return f"Completed todo item {action.index}", False
            else:
                return "Complete operation requires index", True
        elif action.operation == "remove":
            if action.index is not None:
                self.todo_manager.remove_item(action.index)
                return f"Removed todo item {action.index}", False
            else:
                return "Remove operation requires index", True
        else:
            return f"Unknown todo operation: {action.operation}", True
    
    def _handle_finish_stage(self, action: FinishStageAction) -> Tuple[str, bool]:
        """Handle FinishStageAction."""
        return f"Stage finished: {action.message}", False
    
    def _extract_task_response(self, task) -> str:
        """Extract response text from Bindu task."""
        # Get the last message in the task
        if task.messages and len(task.messages) > 0:
            last_message = task.messages[-1]
            if hasattr(last_message, 'text'):
                return last_message.text
            elif isinstance(last_message, dict):
                return last_message.get('text', str(last_message))
        
        return str(task.result) if task.result else "No response"
    
    def get_and_clear_agent_trajectories(self) -> Dict[str, Dict[str, Any]]:
        """Get and clear agent trajectories."""
        trajectories = self.agent_trajectories.copy()
        self.agent_trajectories.clear()
        return trajectories
