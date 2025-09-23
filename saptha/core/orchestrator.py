"""
Core orchestrator that coordinates distributed agents using A2A protocol.
Based on Agno Team reasoning logic but adapted for distributed architecture.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog

from ..context.manager import ContextManager
from ..core.types import (
    AgentInfo,
    AgentResponse,
    ConversationContext,
    ExecutionMode,
    Message,
    TaskRequest,
    TaskResult,
    TaskStatus,
)
from ..protocol.a2a_client import A2AClient, AgentUnavailableError, A2AClientError
from ..routing.router import TaskRouter

logger = structlog.get_logger(__name__)


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class NoAgentsAvailableError(OrchestratorError):
    """Raised when no agents are available for a task."""
    pass


class TaskExecutionError(OrchestratorError):
    """Raised when task execution fails."""
    pass


class DistributedOrchestrator:
    """
    Distributed agent orchestrator using A2A protocol.
    
    This class implements the core team reasoning logic from Agno,
    adapted for distributed agents communicating via A2A protocol.
    
    Key responsibilities:
    - Task routing and agent selection
    - Coordinating agent execution (sequential, parallel, collaborative)
    - Managing conversation context
    - Aggregating and processing responses
    """
    
    def __init__(
        self,
        context_manager: ContextManager,
        task_router: Optional[TaskRouter] = None,
        max_concurrent_agents: int = 5,
        default_timeout: float = 30.0
    ):
        self.context_manager = context_manager
        self.task_router = task_router or TaskRouter()
        self.max_concurrent_agents = max_concurrent_agents
        self.default_timeout = default_timeout
        
        # Agent client cache
        self._agent_clients: Dict[str, A2AClient] = {}
        
        self.logger = logger.bind(component="orchestrator")
    
    async def initialize(self) -> None:
        """Initialize the orchestrator."""
        await self.context_manager.initialize()
        self.logger.info("Orchestrator initialized")
    
    async def close(self) -> None:
        """Close the orchestrator and cleanup resources."""
        # Close all agent clients
        for client in self._agent_clients.values():
            await client.close()
        self._agent_clients.clear()
        
        await self.context_manager.close()
        self.logger.info("Orchestrator closed")
    
    def _get_agent_client(self, agent_info: AgentInfo) -> A2AClient:
        """Get or create an A2A client for an agent."""
        if agent_info.id not in self._agent_clients:
            self._agent_clients[agent_info.id] = A2AClient(
                agent_id=agent_info.id,
                base_url=agent_info.endpoint,
                timeout=self.default_timeout
            )
        return self._agent_clients[agent_info.id]
    
    async def process_message(
        self,
        message: Message,
        context_id: Optional[str] = None,
        execution_mode: Optional[ExecutionMode] = None,
        max_agents: Optional[int] = None
    ) -> TaskResult:
        """
        Process a message by coordinating distributed agents.
        
        Args:
            message: The message to process
            context_id: Optional conversation context ID
            execution_mode: How agents should be executed
            max_agents: Maximum number of agents to use
            
        Returns:
            TaskResult with the final response
        """
        start_time = time.time()
        
        # Create or get context
        if context_id is None:
            context_id = str(uuid.uuid4())
        
        context = await self.context_manager.get_context(context_id)
        if context is None:
            context = await self.context_manager.create_context(context_id)
        
        # Add message to context
        await self.context_manager.add_message(context_id, message)
        
        # Analyze task requirements
        required_capabilities = self.task_router.analyze_task_requirements(message.content)
        
        # Determine execution mode if not provided
        if execution_mode is None:
            execution_mode = self.task_router.determine_execution_mode(
                message.content, required_capabilities
            )
        
        # Create task request
        task_request = TaskRequest(
            message=message,
            context_id=context_id,
            required_capabilities=required_capabilities,
            execution_mode=execution_mode,
            max_agents=max_agents
        )
        
        self.logger.info(
            "Processing message",
            task_id=task_request.id,
            context_id=context_id,
            execution_mode=execution_mode.value,
            required_capabilities=[cap.value for cap in required_capabilities]
        )
        
        try:
            # Create task in database
            task_result = await self.context_manager.create_task(task_request)
            
            # Execute task
            final_response = await self._execute_task(task_request, context)
            
            # Complete task
            execution_time = time.time() - start_time
            await self.context_manager.complete_task(
                task_request.id,
                final_response,
                execution_time
            )
            
            # Get final task result
            completed_task = await self.context_manager.get_task(task_request.id)
            
            self.logger.info(
                "Completed message processing",
                task_id=task_request.id,
                execution_time=execution_time,
                agent_count=len(completed_task.agent_responses) if completed_task else 0
            )
            
            return completed_task or task_result
            
        except Exception as e:
            # Mark task as failed
            await self.context_manager.update_task_status(
                task_request.id,
                TaskStatus.FAILED,
                str(e)
            )
            
            self.logger.error(
                "Failed to process message",
                task_id=task_request.id,
                error=str(e),
                execution_time=time.time() - start_time
            )
            raise TaskExecutionError(f"Task execution failed: {str(e)}")
    
    async def _execute_task(
        self,
        task_request: TaskRequest,
        context: ConversationContext
    ) -> str:
        """Execute a task using the appropriate coordination strategy."""
        # Update task status
        await self.context_manager.update_task_status(task_request.id, TaskStatus.ROUTING)
        
        # Get available agents
        available_agents = await self.context_manager.get_available_agents()
        if not available_agents:
            raise NoAgentsAvailableError("No agents are currently available")
        
        # Route task to agents
        selected_agents = await self.task_router.route_task(task_request, available_agents)
        
        # Update task status
        await self.context_manager.update_task_status(task_request.id, TaskStatus.EXECUTING)
        
        # Execute based on mode
        if task_request.execution_mode == ExecutionMode.SEQUENTIAL:
            return await self._execute_sequential(task_request, selected_agents, context)
        elif task_request.execution_mode == ExecutionMode.PARALLEL:
            return await self._execute_parallel(task_request, selected_agents, context)
        elif task_request.execution_mode == ExecutionMode.COLLABORATIVE:
            return await self._execute_collaborative(task_request, selected_agents, context)
        else:
            raise ValueError(f"Unknown execution mode: {task_request.execution_mode}")
    
    async def _execute_sequential(
        self,
        task_request: TaskRequest,
        agents: List[AgentInfo],
        context: ConversationContext
    ) -> str:
        """Execute agents sequentially, passing results between them."""
        current_message = task_request.message
        final_response = ""
        
        for i, agent in enumerate(agents):
            self.logger.debug(
                "Executing agent sequentially",
                task_id=task_request.id,
                agent_id=agent.id,
                step=i + 1,
                total_steps=len(agents)
            )
            
            try:
                client = self._get_agent_client(agent)
                response = await client.send_message(
                    current_message,
                    context_id=task_request.context_id,
                    metadata={"task_id": str(task_request.id), "step": i + 1}
                )
                
                # Store response
                await self.context_manager.add_agent_response(response)
                
                # Update message for next agent (if any)
                if i < len(agents) - 1:
                    current_message = Message(
                        content=f"Previous agent response: {response.content}\n\nOriginal request: {task_request.message.content}",
                        role="system"
                    )
                else:
                    final_response = response.content
                
                # Notify router of completion
                self.task_router.agent_completed_task(agent.id)
                
            except (AgentUnavailableError, A2AClientError) as e:
                self.logger.error(
                    "Agent failed in sequential execution",
                    task_id=task_request.id,
                    agent_id=agent.id,
                    error=str(e)
                )
                
                # For sequential execution, if a critical agent fails, we fail the task
                error_response = AgentResponse(
                    agent_id=agent.id,
                    task_id=task_request.id,
                    content="",
                    success=False,
                    error_message=str(e)
                )
                await self.context_manager.add_agent_response(error_response)
                raise TaskExecutionError(f"Critical agent {agent.id} failed: {str(e)}")
        
        return final_response
    
    async def _execute_parallel(
        self,
        task_request: TaskRequest,
        agents: List[AgentInfo],
        context: ConversationContext
    ) -> str:
        """Execute agents in parallel and aggregate responses."""
        self.logger.debug(
            "Executing agents in parallel",
            task_id=task_request.id,
            agent_count=len(agents)
        )
        
        # Create tasks for all agents
        agent_tasks = []
        for agent in agents:
            task = self._execute_single_agent(
                agent,
                task_request.message,
                task_request.context_id,
                task_request.id
            )
            agent_tasks.append(task)
        
        # Wait for all agents to complete (or timeout)
        try:
            responses = await asyncio.gather(*agent_tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error("Error in parallel execution", task_id=task_request.id, error=str(e))
            raise TaskExecutionError(f"Parallel execution failed: {str(e)}")
        
        # Process responses
        successful_responses = []
        failed_agents = []
        
        for i, response in enumerate(responses):
            agent = agents[i]
            
            if isinstance(response, Exception):
                self.logger.warning(
                    "Agent failed in parallel execution",
                    task_id=task_request.id,
                    agent_id=agent.id,
                    error=str(response)
                )
                
                error_response = AgentResponse(
                    agent_id=agent.id,
                    task_id=task_request.id,
                    content="",
                    success=False,
                    error_message=str(response)
                )
                await self.context_manager.add_agent_response(error_response)
                failed_agents.append(agent.id)
            else:
                await self.context_manager.add_agent_response(response)
                successful_responses.append(response)
                self.task_router.agent_completed_task(agent.id)
        
        # Aggregate successful responses
        if not successful_responses:
            raise TaskExecutionError("All agents failed in parallel execution")
        
        return self._aggregate_responses(successful_responses, task_request)
    
    async def _execute_collaborative(
        self,
        task_request: TaskRequest,
        agents: List[AgentInfo],
        context: ConversationContext
    ) -> str:
        """Execute agents collaboratively with iterative refinement."""
        # For now, implement as sequential with response building
        # In a more sophisticated implementation, this could involve
        # multiple rounds of agent interaction
        
        self.logger.debug(
            "Executing agents collaboratively",
            task_id=task_request.id,
            agent_count=len(agents)
        )
        
        # Start with the original message
        working_content = task_request.message.content
        responses = []
        
        for i, agent in enumerate(agents):
            # Create a collaborative message that includes previous work
            if responses:
                previous_work = "\n\n".join([
                    f"Agent {resp.agent_id}: {resp.content}"
                    for resp in responses
                ])
                collaborative_message = Message(
                    content=f"Original request: {task_request.message.content}\n\nPrevious work:\n{previous_work}\n\nPlease build upon this work and provide your contribution:",
                    role="system"
                )
            else:
                collaborative_message = task_request.message
            
            try:
                client = self._get_agent_client(agent)
                response = await client.send_message(
                    collaborative_message,
                    context_id=task_request.context_id,
                    metadata={"task_id": str(task_request.id), "collaboration_step": i + 1}
                )
                
                await self.context_manager.add_agent_response(response)
                responses.append(response)
                self.task_router.agent_completed_task(agent.id)
                
            except (AgentUnavailableError, A2AClientError) as e:
                self.logger.warning(
                    "Agent failed in collaborative execution",
                    task_id=task_request.id,
                    agent_id=agent.id,
                    error=str(e)
                )
                
                error_response = AgentResponse(
                    agent_id=agent.id,
                    task_id=task_request.id,
                    content="",
                    success=False,
                    error_message=str(e)
                )
                await self.context_manager.add_agent_response(error_response)
        
        if not responses:
            raise TaskExecutionError("All agents failed in collaborative execution")
        
        # For collaborative mode, return the final refined response
        return responses[-1].content
    
    async def _execute_single_agent(
        self,
        agent: AgentInfo,
        message: Message,
        context_id: Optional[str],
        task_id: UUID
    ) -> AgentResponse:
        """Execute a single agent and return its response."""
        try:
            client = self._get_agent_client(agent)
            response = await client.send_message(
                message,
                context_id=context_id,
                metadata={"task_id": str(task_id)}
            )
            return response
            
        except Exception as e:
            self.logger.error(
                "Single agent execution failed",
                agent_id=agent.id,
                task_id=task_id,
                error=str(e)
            )
            raise
    
    def _aggregate_responses(
        self,
        responses: List[AgentResponse],
        task_request: TaskRequest
    ) -> str:
        """
        Aggregate multiple agent responses into a final response.
        
        This is a simple implementation. In production, you might use
        more sophisticated aggregation strategies.
        """
        if len(responses) == 1:
            return responses[0].content
        
        # Create a combined response
        combined_parts = []
        for i, response in enumerate(responses, 1):
            combined_parts.append(f"Agent {response.agent_id} Response:\n{response.content}")
        
        return "\n\n---\n\n".join(combined_parts)
    
    async def health_check_agents(self) -> Dict[str, bool]:
        """Perform health checks on all registered agents."""
        agents = await self.context_manager.get_available_agents()
        health_results = {}
        
        for agent in agents:
            try:
                client = self._get_agent_client(agent)
                is_healthy = await client.health_check()
                health_results[agent.id] = is_healthy
                
                # Update availability in database
                await self.context_manager.update_agent_availability(agent.id, is_healthy)
                
            except Exception as e:
                self.logger.warning(
                    "Health check failed for agent",
                    agent_id=agent.id,
                    error=str(e)
                )
                health_results[agent.id] = False
                await self.context_manager.update_agent_availability(agent.id, False)
        
        return health_results
