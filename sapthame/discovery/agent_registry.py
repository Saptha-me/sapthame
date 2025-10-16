"""Agent discovery and registry management."""

import logging
from typing import Dict, List, Optional

from src.protocol.a2a_client import A2AClient
from src.discovery.entities.agent_info import AgentInfo

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Central registry for discovered agents."""
    
    def __init__(self, a2a_client: A2AClient):
        """Initialize agent registry.
        
        Args:
            a2a_client: A2A client for fetching agent info
        """
        self.a2a_client = a2a_client
        self.agents: Dict[str, AgentInfo] = {}
        self.skill_index: Dict[str, List[str]] = {}  # skill_name -> agent_ids
    
    def discover_agents(self, agent_urls: List[str]):
        """Discover agents from their get-info.json endpoints.
        
        Args:
            agent_urls: List of agent URLs or get-info.json URLs
        """
        for url in agent_urls:
            try:
                info_data = self.a2a_client.fetch_agent_info(url)
                agent_info = AgentInfo.from_dict(info_data)
                self.add_agent(agent_info)
                logger.info(f"✓ Discovered agent: {agent_info.name} ({agent_info.id})")
            except Exception as e:
                logger.error(f"✗ Failed to discover agent at {url}: {e}")
    
    def add_agent(self, agent_info: AgentInfo):
        """Add agent to registry and index its skills.
        
        Args:
            agent_info: Agent information
        """
        self.agents[agent_info.id] = agent_info
        
        # Index skills
        for skill in agent_info.skills:
            if skill.name not in self.skill_index:
                self.skill_index[skill.name] = []
            self.skill_index[skill.name].append(agent_info.id)
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            AgentInfo or None if not found
        """
        return self.agents.get(agent_id)
    
    def get_agents_by_skill(self, skill_name: str) -> List[AgentInfo]:
        """Get all agents with a specific skill.
        
        Args:
            skill_name: Skill to search for
            
        Returns:
            List of agents with the skill
        """
        agent_ids = self.skill_index.get(skill_name, [])
        return [self.agents[aid] for aid in agent_ids if aid in self.agents]
    
    def get_all_agents(self) -> List[AgentInfo]:
        """Get all registered agents.
        
        Returns:
            List of all agents
        """
        return list(self.agents.values())
    
    def view_all_agents(self) -> str:
        """Return formatted view of all agents.
        
        Returns:
            Formatted string of all agents
        """
        if not self.agents:
            return "No agents discovered."
        
        lines = ["Available Agents:"]
        for agent_id, agent in self.agents.items():
            lines.append(f"\n  [{agent_id}] {agent.name}")
            lines.append(f"      Description: {agent.description}")
            lines.append(f"      URL: {agent.url}")
            lines.append(f"      Skills: {', '.join(agent.get_skill_names())}")
            
            specialization = agent.extra_data.get('specialization', 'N/A')
            lines.append(f"      Specialization: {specialization}")
            lines.append(f"      Trust Level: {agent.agent_trust}")
        
        return "\n".join(lines)
    
