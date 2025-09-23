"""
Task routing system for selecting and coordinating agents.
"""

from __future__ import annotations

import asyncio
from typing import List, Optional, Set
from uuid import UUID

import structlog

from ..core.types import (
    AgentCapability,
    AgentInfo,
    ExecutionMode,
    TaskRequest,
)

logger = structlog.get_logger(__name__)


class AgentSelectionStrategy:
    """Base class for agent selection strategies."""
    
    def select_agents(
        self,
        task_request: TaskRequest,
        available_agents: List[AgentInfo]
    ) -> List[AgentInfo]:
        """Select agents for a task."""
        raise NotImplementedError


class CapabilityBasedStrategy(AgentSelectionStrategy):
    """Select agents based on required capabilities."""
    
    def select_agents(
        self,
        task_request: TaskRequest,
        available_agents: List[AgentInfo]
    ) -> List[AgentInfo]:
        """
        Select agents that have the required capabilities.
        
        Args:
            task_request: The task requiring agents
            available_agents: List of available agents
            
        Returns:
            List of selected agents
        """
        if not task_request.required_capabilities:
            # If no specific capabilities required, select based on execution mode
            if task_request.execution_mode == ExecutionMode.PARALLEL:
                # For parallel execution, select multiple agents
                selected = available_agents[:task_request.max_agents or 3]
            else:
                # For sequential/collaborative, start with one general agent
                selected = available_agents[:1]
        else:
            # Filter agents by required capabilities
            required_caps = set(task_request.required_capabilities)
            selected = []
            
            for agent in available_agents:
                agent_caps = set(agent.capabilities)
                if required_caps.intersection(agent_caps):
                    selected.append(agent)
                    
                    # Stop if we have enough agents
                    if task_request.max_agents and len(selected) >= task_request.max_agents:
                        break
        
        return selected


class LoadBalancedStrategy(AgentSelectionStrategy):
    """Select agents with load balancing considerations."""
    
    def __init__(self):
        self._agent_load: dict[str, int] = {}
    
    def select_agents(
        self,
        task_request: TaskRequest,
        available_agents: List[AgentInfo]
    ) -> List[AgentInfo]:
        """Select agents considering current load."""
        # First filter by capabilities
        capability_strategy = CapabilityBasedStrategy()
        capable_agents = capability_strategy.select_agents(task_request, available_agents)
        
        # Sort by current load (ascending)
        capable_agents.sort(key=lambda agent: self._agent_load.get(agent.id, 0))
        
        # Select based on execution mode and max agents
        max_agents = task_request.max_agents or (3 if task_request.execution_mode == ExecutionMode.PARALLEL else 1)
        selected = capable_agents[:max_agents]
        
        # Update load tracking
        for agent in selected:
            self._agent_load[agent.id] = self._agent_load.get(agent.id, 0) + 1
        
        return selected
    
    def agent_completed_task(self, agent_id: str) -> None:
        """Decrease load count for an agent."""
        if agent_id in self._agent_load:
            self._agent_load[agent_id] = max(0, self._agent_load[agent_id] - 1)


class TaskRouter:
    """
    Routes tasks to appropriate agents based on capabilities and strategy.
    
    This class implements the core routing logic that determines:
    - Which agents should handle a task
    - How agents should be coordinated
    - Load balancing and availability
    """
    
    def __init__(self, strategy: Optional[AgentSelectionStrategy] = None):
        self.strategy = strategy or LoadBalancedStrategy()
        self.logger = logger.bind(component="task_router")
    
    async def route_task(
        self,
        task_request: TaskRequest,
        available_agents: List[AgentInfo]
    ) -> List[AgentInfo]:
        """
        Route a task to appropriate agents.
        
        Args:
            task_request: The task to route
            available_agents: List of available agents
            
        Returns:
            List of selected agents for the task
            
        Raises:
            ValueError: If no suitable agents are found
        """
        if not available_agents:
            raise ValueError("No agents available for task routing")
        
        # Select agents using the configured strategy
        selected_agents = self.strategy.select_agents(task_request, available_agents)
        
        if not selected_agents:
            self.logger.warning(
                "No suitable agents found for task",
                task_id=task_request.id,
                required_capabilities=[cap.value for cap in task_request.required_capabilities],
                available_agents=[agent.id for agent in available_agents]
            )
            raise ValueError("No suitable agents found for the requested capabilities")
        
        self.logger.info(
            "Routed task to agents",
            task_id=task_request.id,
            selected_agents=[agent.id for agent in selected_agents],
            execution_mode=task_request.execution_mode.value
        )
        
        return selected_agents
    
    def analyze_task_requirements(self, task_content: str) -> List[AgentCapability]:
        """
        Analyze task content to determine required capabilities.
        
        This is a simple heuristic-based approach. In a production system,
        you might use ML models or more sophisticated NLP techniques.
        
        Args:
            task_content: The content of the task
            
        Returns:
            List of inferred capabilities
        """
        content_lower = task_content.lower()
        capabilities = []
        
        # Web search indicators
        if any(keyword in content_lower for keyword in [
            "search", "find online", "web", "internet", "latest", "current", "news"
        ]):
            capabilities.append(AgentCapability.WEB_SEARCH)
        
        # Knowledge base indicators
        if any(keyword in content_lower for keyword in [
            "explain", "define", "what is", "tell me about", "knowledge", "information"
        ]):
            capabilities.append(AgentCapability.KNOWLEDGE_BASE)
        
        # Data analysis indicators
        if any(keyword in content_lower for keyword in [
            "analyze", "calculate", "statistics", "data", "chart", "graph", "trend"
        ]):
            capabilities.append(AgentCapability.DATA_ANALYSIS)
        
        # Code generation indicators
        if any(keyword in content_lower for keyword in [
            "code", "program", "function", "script", "algorithm", "implement"
        ]):
            capabilities.append(AgentCapability.CODE_GENERATION)
        
        # Text processing indicators
        if any(keyword in content_lower for keyword in [
            "summarize", "translate", "rewrite", "edit", "format", "text"
        ]):
            capabilities.append(AgentCapability.TEXT_PROCESSING)
        
        # Image processing indicators
        if any(keyword in content_lower for keyword in [
            "image", "picture", "photo", "visual", "draw", "generate image"
        ]):
            capabilities.append(AgentCapability.IMAGE_PROCESSING)
        
        # Reasoning indicators
        if any(keyword in content_lower for keyword in [
            "think", "reason", "logic", "solve", "problem", "decision", "plan"
        ]):
            capabilities.append(AgentCapability.REASONING)
        
        # If no specific capabilities detected, default to reasoning
        if not capabilities:
            capabilities.append(AgentCapability.REASONING)
        
        self.logger.debug(
            "Analyzed task requirements",
            task_content=task_content[:100] + "..." if len(task_content) > 100 else task_content,
            inferred_capabilities=[cap.value for cap in capabilities]
        )
        
        return capabilities
    
    def determine_execution_mode(
        self,
        task_content: str,
        required_capabilities: List[AgentCapability]
    ) -> ExecutionMode:
        """
        Determine the best execution mode for a task.
        
        Args:
            task_content: The content of the task
            required_capabilities: Required capabilities for the task
            
        Returns:
            Recommended execution mode
        """
        content_lower = task_content.lower()
        
        # Collaborative indicators
        if any(keyword in content_lower for keyword in [
            "compare", "combine", "merge", "collaborate", "work together"
        ]):
            return ExecutionMode.COLLABORATIVE
        
        # Parallel indicators
        if any(keyword in content_lower for keyword in [
            "multiple", "various", "different approaches", "alternatives"
        ]) or len(required_capabilities) > 2:
            return ExecutionMode.PARALLEL
        
        # Default to sequential for most tasks
        return ExecutionMode.SEQUENTIAL
    
    def agent_completed_task(self, agent_id: str) -> None:
        """Notify router that an agent completed a task (for load balancing)."""
        if isinstance(self.strategy, LoadBalancedStrategy):
            self.strategy.agent_completed_task(agent_id)
