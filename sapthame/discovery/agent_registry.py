"""Agent registry for managing Bindu client URLs."""

import logging
from typing import Dict, List

from .protocol.bindu_client import BinduClient

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry for Bindu agent clients."""
    
    def __init__(self, agent_urls: List[str]):
        """Initialize agent registry with client URLs.
        
        Args:
            agent_urls: List of agent base URLs
        """
        self.clients: Dict[str, BinduClient] = {}
        
        for url in agent_urls:
            try:
                client = BinduClient(agent_url=url)
                self.clients[url] = client
                logger.info(f"✓ Registered agent: {url}")
            except Exception as e:
                logger.error(f"✗ Failed to register agent at {url}: {e}")
    
    def get_client(self, url: str) -> BinduClient:
        """Get Bindu client by URL.
        
        Args:
            url: Agent URL
            
        Returns:
            BinduClient instance
        """
        return self.clients.get(url)
    
    def get_all_clients(self) -> List[BinduClient]:
        """Get all registered clients.
        
        Returns:
            List of BinduClient instances
        """
        return list(self.clients.values())
    
    def get_urls(self) -> List[str]:
        """Get all registered agent URLs.
        
        Returns:
            List of agent URLs
        """
        return list(self.clients.keys())
