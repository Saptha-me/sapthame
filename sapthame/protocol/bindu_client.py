"""Bindu protocol client for agent communication following A2A Task-First pattern."""

import logging
import requests
import time
from typing import Dict, Optional, List

from sapthame.protocol.entities.bindu_message import BinduMessage, MessageConfiguration
from sapthame.protocol.entities.bindu_task import BinduTask
from sapthame.protocol.entities.jsonrpc import JSONRPCRequest, JSONRPCResponse
from sapthame.protocol.state_manager import TaskStateManager

logger = logging.getLogger(__name__)


class BinduClient:
    """Client for Bindu protocol communication with agents.
    
    Implements A2A Task-First pattern with JSON-RPC 2.0.
    """
    
    def __init__(self, agent_url: str, timeout: int = 30, auth_token: Optional[str] = None):
        """Initialize Bindu client.
        
        Args:
            agent_url: Agent's base URL
            timeout: Request timeout in seconds
            auth_token: Optional bearer token for authentication
        """
        self.agent_url = agent_url.rstrip('/')
        self.timeout = timeout
        self.auth_token = auth_token
        self.state_manager = TaskStateManager()
        
        # Try to fetch agent info
        try:
            self.info = self.fetch_agent_info()
            logger.info(f"Connected to agent: {self.info.get('name', 'Unknown')}")
        except Exception as e:
            logger.warning(f"Could not fetch agent info: {e}")
            self.info = {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional authentication.
        
        Returns:
            Headers dictionary
        """
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    def fetch_agent_info(self) -> Dict:
        """Fetch agent's get-info.json.
            
        Returns:
            Agent info dictionary
        """
        url = f"{self.agent_url}/get-info.json"
        logger.info(f"Fetching agent info from {url}")
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch agent info from {url}: {e}")
            raise
    
    def _send_jsonrpc_request(self, method: str, params: Dict) -> JSONRPCResponse:
        """Send JSON-RPC 2.0 request to agent.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            
        Returns:
            JSONRPCResponse
        """
        request = JSONRPCRequest(method=method, params=params)
        
        logger.debug(f"Sending JSON-RPC request: {method}")
        
        try:
            response = requests.post(
                self.agent_url,
                json=request.to_dict(),
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            jsonrpc_response = JSONRPCResponse.from_dict(response_data)
            
            if not jsonrpc_response.is_success():
                logger.error(f"JSON-RPC error: {jsonrpc_response.error}")
            
            return jsonrpc_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send JSON-RPC request: {e}")
            raise
    
    def send_message(
        self,
        text: str,
        context_id: Optional[str] = None,
        task_id: Optional[str] = None,
        reference_task_ids: Optional[List[str]] = None,
        accepted_output_modes: Optional[List[str]] = None
    ) -> BinduTask:
        """Send message to agent using Bindu protocol.
        
        Args:
            text: Message text
            context_id: Optional context ID for conversation continuity
            task_id: Optional task ID (generated if not provided)
            reference_task_ids: Optional list of reference task IDs
            accepted_output_modes: Optional list of accepted output MIME types
            
        Returns:
            BinduTask with initial response
        """
        # Create message
        message = BinduMessage.create_text_message(
            text=text,
            context_id=context_id,
            task_id=task_id,
            reference_task_ids=reference_task_ids
        )
        
        # Create configuration
        config = MessageConfiguration(
            acceptedOutputModes=accepted_output_modes or ["application/json"]
        )
        
        # Send via JSON-RPC
        params = {
            "message": message.to_dict(),
            "configuration": config.to_dict()
        }
        
        logger.info(f"Sending message to task {message.taskId}")
        logger.debug(f"Message: {text[:100]}...")
        
        response = self._send_jsonrpc_request("message/send", params)
        
        if not response.is_success():
            raise Exception(f"Failed to send message: {response.error}")
        
        # Parse task from response
        task_data = response.result.get("task", {})
        task = BinduTask.from_dict(task_data)
        
        # Track in state manager
        self.state_manager.add_task(task)
        
        logger.info(f"Task {task.taskId} created with state: {task.state}")
        return task
    
    def get_task(self, task_id: str) -> BinduTask:
        """Get task status and details.
        
        Args:
            task_id: Task ID
            
        Returns:
            BinduTask with current state
        """
        params = {"taskId": task_id}
        
        logger.debug(f"Fetching task {task_id}")
        
        response = self._send_jsonrpc_request("tasks/get", params)
        
        if not response.is_success():
            raise Exception(f"Failed to get task: {response.error}")
        
        task_data = response.result.get("task", {})
        task = BinduTask.from_dict(task_data)
        
        # Update state manager
        self.state_manager.add_task(task)
        
        return task
    
    def list_tasks(self, context_id: Optional[str] = None) -> List[BinduTask]:
        """List tasks, optionally filtered by context.
        
        Args:
            context_id: Optional context ID to filter by
            
        Returns:
            List of tasks
        """
        params = {}
        if context_id:
            params["contextId"] = context_id
        
        response = self._send_jsonrpc_request("tasks/list", params)
        
        if not response.is_success():
            raise Exception(f"Failed to list tasks: {response.error}")
        
        tasks_data = response.result.get("tasks", [])
        tasks = [BinduTask.from_dict(td) for td in tasks_data]
        
        # Update state manager
        for task in tasks:
            self.state_manager.add_task(task)
        
        return tasks
    
    def cancel_task(self, task_id: str) -> BinduTask:
        """Cancel a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Updated task
        """
        params = {"taskId": task_id}
        
        logger.info(f"Canceling task {task_id}")
        
        response = self._send_jsonrpc_request("tasks/cancel", params)
        
        if not response.is_success():
            raise Exception(f"Failed to cancel task: {response.error}")
        
        task_data = response.result.get("task", {})
        task = BinduTask.from_dict(task_data)
        
        # Update state manager
        self.state_manager.add_task(task)
        
        return task
    
    def wait_for_task(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0
    ) -> BinduTask:
        """Wait for task to reach terminal state.
        
        Args:
            task_id: Task ID
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            
        Returns:
            Final task state
            
        Raises:
            TimeoutError: If max_wait exceeded
        """
        start_time = time.time()
        
        logger.info(f"Waiting for task {task_id} to complete")
        
        while True:
            task = self.get_task(task_id)
            
            if task.is_terminal():
                logger.info(f"Task {task_id} reached terminal state: {task.state}")
                return task
            
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(f"Task {task_id} did not complete within {max_wait}s")
            
            logger.debug(f"Task {task_id} still {task.state}, waiting...")
            time.sleep(poll_interval)
    
    def send_and_wait(
        self,
        text: str,
        context_id: Optional[str] = None,
        reference_task_ids: Optional[List[str]] = None,
        poll_interval: float = 2.0,
        max_wait: float = 300.0
    ) -> BinduTask:
        """Send message and wait for completion.
        
        Args:
            text: Message text
            context_id: Optional context ID
            reference_task_ids: Optional reference task IDs
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait
            
        Returns:
            Completed task
        """
        task = self.send_message(
            text=text,
            context_id=context_id,
            reference_task_ids=reference_task_ids
        )
        
        return self.wait_for_task(
            task_id=task.taskId,
            poll_interval=poll_interval,
            max_wait=max_wait
        )
