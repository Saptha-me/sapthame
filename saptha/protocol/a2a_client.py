"""
A2A Protocol client for communicating with distributed agents.
Based on FastA2A client with extensions for orchestration.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

import httpx
import structlog
from pydantic import BaseModel, TypeAdapter
from tenacity import retry, stop_after_attempt, wait_exponential

from ..core.types import AgentResponse, Message

logger = structlog.get_logger(__name__)


class A2AMessage(BaseModel):
    """A2A Protocol message format."""
    content: str
    role: str = "user"
    context_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class A2ARequest(BaseModel):
    """A2A Protocol request."""
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Dict[str, Any]


class A2AResponse(BaseModel):
    """A2A Protocol response."""
    jsonrpc: str = "2.0"
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class A2AClientError(Exception):
    """Base exception for A2A client errors."""
    pass


class AgentUnavailableError(A2AClientError):
    """Raised when an agent is unavailable."""
    pass


class A2AClient:
    """
    A2A Protocol client for communicating with agent servers.
    
    This client extends the basic FastA2A functionality with:
    - Retry logic for reliability
    - Structured logging
    - Agent-specific error handling
    - Context management
    """
    
    def __init__(
        self,
        agent_id: str,
        base_url: str,
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None
    ) -> None:
        self.agent_id = agent_id
        self.base_url = base_url
        self.timeout = timeout
        
        if http_client is None:
            self.http_client = httpx.AsyncClient(
                base_url=base_url,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
        else:
            self.http_client = http_client
            if hasattr(http_client, 'base_url'):
                self.http_client.base_url = base_url
        
        self.logger = logger.bind(agent_id=agent_id, base_url=base_url)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    async def send_message(
        self,
        message: Message,
        context_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Send a message to the agent and get a response.
        
        Args:
            message: The message to send
            context_id: Optional context identifier
            metadata: Additional metadata
            
        Returns:
            AgentResponse from the agent
            
        Raises:
            AgentUnavailableError: If agent is not available
            A2AClientError: For other communication errors
        """
        request_id = str(uuid.uuid4())
        
        a2a_message = A2AMessage(
            content=message.content,
            role=message.role,
            context_id=context_id,
            metadata=metadata or {}
        )
        
        request = A2ARequest(
            id=request_id,
            method="message/send",
            params={
                "message": a2a_message.model_dump(),
                "metadata": metadata or {}
            }
        )
        
        self.logger.debug(
            "Sending message to agent",
            request_id=request_id,
            message_content=message.content[:100] + "..." if len(message.content) > 100 else message.content
        )
        
        try:
            response = await self.http_client.post(
                "/",
                content=request.model_dump_json(),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code >= 500:
                raise AgentUnavailableError(f"Agent {self.agent_id} returned server error: {response.status_code}")
            elif response.status_code >= 400:
                raise A2AClientError(f"Client error: {response.status_code} - {response.text}")
            
            a2a_response = A2AResponse.model_validate_json(response.content)
            
            if a2a_response.error:
                error_msg = a2a_response.error.get("message", "Unknown error")
                self.logger.error("Agent returned error", error=error_msg, request_id=request_id)
                raise A2AClientError(f"Agent error: {error_msg}")
            
            if not a2a_response.result:
                raise A2AClientError("Agent returned empty result")
            
            # Convert A2A response to AgentResponse
            agent_response = AgentResponse(
                agent_id=self.agent_id,
                task_id=message.id,
                content=a2a_response.result.get("content", ""),
                success=True,
                metadata=a2a_response.result.get("metadata", {})
            )
            
            self.logger.debug(
                "Received response from agent",
                request_id=request_id,
                response_length=len(agent_response.content)
            )
            
            return agent_response
            
        except httpx.TimeoutException:
            self.logger.error("Timeout communicating with agent", request_id=request_id)
            raise AgentUnavailableError(f"Agent {self.agent_id} timed out")
        except httpx.ConnectError:
            self.logger.error("Failed to connect to agent", request_id=request_id)
            raise AgentUnavailableError(f"Cannot connect to agent {self.agent_id}")
        except Exception as e:
            self.logger.error("Unexpected error communicating with agent", error=str(e), request_id=request_id)
            raise A2AClientError(f"Unexpected error: {str(e)}")
    
    async def health_check(self) -> bool:
        """
        Check if the agent is healthy and available.
        
        Returns:
            True if agent is healthy, False otherwise
        """
        try:
            request = A2ARequest(
                id=str(uuid.uuid4()),
                method="health/check",
                params={}
            )
            
            response = await self.http_client.post(
                "/health",
                content=request.model_dump_json(),
                timeout=5.0
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.debug("Health check failed", error=str(e))
            return False
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.http_client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
