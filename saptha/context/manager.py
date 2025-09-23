"""
Context manager for handling conversation context and task state.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from ..core.types import (
    AgentInfo,
    AgentResponse,
    ConversationContext,
    Message,
    TaskRequest,
    TaskResult,
    TaskStatus,
)
from .models import (
    AgentInfoModel,
    AgentResponseModel,
    Base,
    ConversationContextModel,
    MessageModel,
    TaskModel,
)

logger = structlog.get_logger(__name__)


class ContextManager:
    """
    Manages conversation context and task state in PostgreSQL.
    
    This class provides a clean interface for:
    - Storing and retrieving conversation contexts
    - Managing task lifecycle
    - Tracking agent responses
    - Maintaining agent registry
    """
    
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.logger = logger.bind(component="context_manager")
    
    async def initialize(self) -> None:
        """Initialize the database schema."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.logger.info("Database schema initialized")
    
    async def close(self) -> None:
        """Close the database connection."""
        await self.engine.dispose()
    
    # Context Management
    
    async def create_context(self, context_id: str, metadata: Optional[Dict[str, Any]] = None) -> ConversationContext:
        """Create a new conversation context."""
        async with self.session_factory() as session:
            context_model = ConversationContextModel(
                id=context_id,
                metadata=metadata or {}
            )
            session.add(context_model)
            await session.commit()
            
            self.logger.debug("Created conversation context", context_id=context_id)
            
            return ConversationContext(
                id=context_id,
                metadata=metadata or {},
                created_at=context_model.created_at,
                updated_at=context_model.updated_at
            )
    
    async def get_context(self, context_id: str) -> Optional[ConversationContext]:
        """Get a conversation context with its messages."""
        async with self.session_factory() as session:
            # Get context
            context_result = await session.execute(
                select(ConversationContextModel).where(ConversationContextModel.id == context_id)
            )
            context_model = context_result.scalar_one_or_none()
            
            if not context_model:
                return None
            
            # Get messages
            messages_result = await session.execute(
                select(MessageModel)
                .where(MessageModel.context_id == context_id)
                .order_by(MessageModel.timestamp)
            )
            message_models = messages_result.scalars().all()
            
            # Get active tasks
            tasks_result = await session.execute(
                select(TaskModel.id)
                .where(
                    TaskModel.context_id == context_id,
                    TaskModel.status.in_([TaskStatus.PENDING, TaskStatus.ROUTING, TaskStatus.EXECUTING])
                )
            )
            active_task_ids = [task_id for task_id in tasks_result.scalars().all()]
            
            messages = [
                Message(
                    id=msg.id,
                    content=msg.content,
                    role=msg.role,
                    timestamp=msg.timestamp,
                    metadata=msg.metadata
                )
                for msg in message_models
            ]
            
            return ConversationContext(
                id=context_id,
                messages=messages,
                active_task_ids=active_task_ids,
                metadata=context_model.metadata,
                created_at=context_model.created_at,
                updated_at=context_model.updated_at
            )
    
    async def add_message(self, context_id: str, message: Message) -> None:
        """Add a message to a conversation context."""
        async with self.session_factory() as session:
            message_model = MessageModel(
                id=message.id,
                context_id=context_id,
                content=message.content,
                role=message.role,
                timestamp=message.timestamp,
                metadata=message.metadata
            )
            session.add(message_model)
            
            # Update context timestamp
            await session.execute(
                update(ConversationContextModel)
                .where(ConversationContextModel.id == context_id)
                .values(updated_at=datetime.utcnow())
            )
            
            await session.commit()
            self.logger.debug("Added message to context", context_id=context_id, message_id=message.id)
    
    # Task Management
    
    async def create_task(self, task_request: TaskRequest) -> TaskResult:
        """Create a new task."""
        async with self.session_factory() as session:
            task_model = TaskModel(
                id=task_request.id,
                context_id=task_request.context_id or str(uuid.uuid4()),
                status=TaskStatus.PENDING,
                message_id=task_request.message.id,
                required_capabilities=[cap.value for cap in task_request.required_capabilities],
                execution_mode=task_request.execution_mode.value,
                max_agents=task_request.max_agents,
                metadata=task_request.metadata
            )
            session.add(task_model)
            await session.commit()
            
            self.logger.debug("Created task", task_id=task_request.id, context_id=task_model.context_id)
            
            return TaskResult(
                task_id=task_request.id,
                status=TaskStatus.PENDING,
                metadata=task_request.metadata
            )
    
    async def update_task_status(self, task_id: UUID, status: TaskStatus, error_message: Optional[str] = None) -> None:
        """Update task status."""
        async with self.session_factory() as session:
            update_values = {"status": status.value, "updated_at": datetime.utcnow()}
            if error_message:
                update_values["error_message"] = error_message
            
            await session.execute(
                update(TaskModel)
                .where(TaskModel.id == task_id)
                .values(**update_values)
            )
            await session.commit()
            
            self.logger.debug("Updated task status", task_id=task_id, status=status.value)
    
    async def complete_task(
        self,
        task_id: UUID,
        final_response: str,
        execution_time: Optional[float] = None
    ) -> None:
        """Mark a task as completed."""
        async with self.session_factory() as session:
            await session.execute(
                update(TaskModel)
                .where(TaskModel.id == task_id)
                .values(
                    status=TaskStatus.COMPLETED.value,
                    final_response=final_response,
                    execution_time=execution_time,
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            
            self.logger.debug("Completed task", task_id=task_id, execution_time=execution_time)
    
    async def get_task(self, task_id: UUID) -> Optional[TaskResult]:
        """Get a task with its responses."""
        async with self.session_factory() as session:
            # Get task
            task_result = await session.execute(
                select(TaskModel).where(TaskModel.id == task_id)
            )
            task_model = task_result.scalar_one_or_none()
            
            if not task_model:
                return None
            
            # Get agent responses
            responses_result = await session.execute(
                select(AgentResponseModel)
                .where(AgentResponseModel.task_id == task_id)
                .order_by(AgentResponseModel.created_at)
            )
            response_models = responses_result.scalars().all()
            
            agent_responses = [
                AgentResponse(
                    agent_id=resp.agent_id,
                    task_id=resp.task_id,
                    content=resp.content,
                    success=resp.success,
                    error_message=resp.error_message,
                    execution_time=resp.execution_time,
                    metadata=resp.metadata
                )
                for resp in response_models
            ]
            
            return TaskResult(
                task_id=task_id,
                status=TaskStatus(task_model.status),
                final_response=task_model.final_response,
                agent_responses=agent_responses,
                execution_time=task_model.execution_time,
                error_message=task_model.error_message,
                metadata=task_model.metadata
            )
    
    async def add_agent_response(self, response: AgentResponse) -> None:
        """Add an agent response to a task."""
        async with self.session_factory() as session:
            response_model = AgentResponseModel(
                task_id=response.task_id,
                agent_id=response.agent_id,
                content=response.content,
                success=response.success,
                error_message=response.error_message,
                execution_time=response.execution_time,
                metadata=response.metadata
            )
            session.add(response_model)
            await session.commit()
            
            self.logger.debug(
                "Added agent response",
                task_id=response.task_id,
                agent_id=response.agent_id,
                success=response.success
            )
    
    # Agent Registry
    
    async def register_agent(self, agent_info: AgentInfo) -> None:
        """Register or update an agent."""
        async with self.session_factory() as session:
            # Check if agent exists
            existing_result = await session.execute(
                select(AgentInfoModel).where(AgentInfoModel.id == agent_info.id)
            )
            existing_agent = existing_result.scalar_one_or_none()
            
            if existing_agent:
                # Update existing agent
                await session.execute(
                    update(AgentInfoModel)
                    .where(AgentInfoModel.id == agent_info.id)
                    .values(
                        name=agent_info.name,
                        description=agent_info.description,
                        capabilities=[cap.value for cap in agent_info.capabilities],
                        endpoint=agent_info.endpoint,
                        is_available=agent_info.is_available,
                        last_health_check=agent_info.last_health_check,
                        metadata=agent_info.metadata,
                        updated_at=datetime.utcnow()
                    )
                )
                self.logger.debug("Updated agent registration", agent_id=agent_info.id)
            else:
                # Create new agent
                agent_model = AgentInfoModel(
                    id=agent_info.id,
                    name=agent_info.name,
                    description=agent_info.description,
                    capabilities=[cap.value for cap in agent_info.capabilities],
                    endpoint=agent_info.endpoint,
                    is_available=agent_info.is_available,
                    last_health_check=agent_info.last_health_check,
                    metadata=agent_info.metadata
                )
                session.add(agent_model)
                self.logger.debug("Registered new agent", agent_id=agent_info.id)
            
            await session.commit()
    
    async def get_available_agents(self) -> List[AgentInfo]:
        """Get all available agents."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(AgentInfoModel).where(AgentInfoModel.is_available == True)
            )
            agent_models = result.scalars().all()
            
            return [
                AgentInfo(
                    id=agent.id,
                    name=agent.name,
                    description=agent.description,
                    capabilities=[cap for cap in agent.capabilities],
                    endpoint=agent.endpoint,
                    is_available=agent.is_available,
                    last_health_check=agent.last_health_check,
                    metadata=agent.metadata
                )
                for agent in agent_models
            ]
    
    async def update_agent_availability(self, agent_id: str, is_available: bool) -> None:
        """Update agent availability status."""
        async with self.session_factory() as session:
            await session.execute(
                update(AgentInfoModel)
                .where(AgentInfoModel.id == agent_id)
                .values(
                    is_available=is_available,
                    last_health_check=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await session.commit()
            
            self.logger.debug("Updated agent availability", agent_id=agent_id, is_available=is_available)
