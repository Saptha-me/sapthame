"""A2A protocol client for agent communication."""

import logging
import requests
from typing import Dict, Optional

from src.protocol.entities.a2a_message import A2AMessage
from src.protocol.entities.a2a_response import A2AResponse

logger = logging.getLogger(__name__)


class A2AClient:
    """Client for A2A protocol communication with agents."""
    
    def __init__(self, timeout: int = 30):
        """Initialize A2A client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    def fetch_agent_info(self, url: str) -> Dict:
        """Fetch agent's get-info.json.
        
        Args:
            url: Base URL or full get-info.json URL
            
        Returns:
            Agent info dictionary
        """
        # Handle both base URL and full get-info.json URL
        if not url.endswith('get-info.json'):
            if not url.endswith('/'):
                url += '/'
            url += 'get-info.json'
        
        logger.info(f"Fetching agent info from {url}")
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch agent info from {url}: {e}")
            raise
    
    def send_message(
        self,
        agent_url: str,
        message: str,
        context: Optional[Dict] = None
    ) -> A2AResponse:
        """Send A2A message to agent.
        
        Args:
            agent_url: Agent's base URL
            message: Message to send
            context: Optional context dictionary
            
        Returns:
            A2AResponse with agent's reply
        """
        # Construct chat endpoint
        if not agent_url.endswith('/'):
            agent_url += '/'
        chat_url = agent_url + 'chat'
        
        # Create message
        a2a_message = A2AMessage(
            message=message,
            context=context or {}
        )
        
        logger.info(f"Sending A2A message to {chat_url}")
        logger.debug(f"Message: {message[:100]}...")
        
        try:
            response = requests.post(
                chat_url,
                json=a2a_message.to_dict(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            a2a_response = A2AResponse.from_dict(response_data)
            
            logger.info(f"Received response from {chat_url}")
            return a2a_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send message to {chat_url}: {e}")
            return A2AResponse(
                content="",
                success=False,
                error=str(e)
            )
