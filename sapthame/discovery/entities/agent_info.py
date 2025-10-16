"""Agent information entity."""

from dataclasses import dataclass, field
from typing import Dict, List, Any

from src.discovery.entities.skill import Skill


@dataclass
class AgentInfo:
    """Information about a discovered agent."""
    
    id: str
    name: str
    description: str
    url: str
    version: str
    protocol_version: str
    skills: List[Skill]
    capabilities: Dict[str, Any]
    extra_data: Dict[str, Any]
    agent_trust: str
    kind: str = "agent"
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentInfo':
        """Create AgentInfo from get-info.json data."""
        skills = [Skill.from_dict(s) for s in data.get('skills', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            url=data['url'],
            version=data['version'],
            protocol_version=data.get('protocolVersion', '1.0'),
            skills=skills,
            capabilities=data.get('capabilities', {}),
            extra_data=data.get('extraData', {}),
            agent_trust=data.get('agentTrust', 'low'),
            kind=data.get('kind', 'agent')
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'url': self.url,
            'version': self.version,
            'protocol_version': self.protocol_version,
            'skills': [s.to_dict() for s in self.skills],
            'capabilities': self.capabilities,
            'extra_data': self.extra_data,
            'agent_trust': self.agent_trust,
            'kind': self.kind
        }
    
    def get_skill_names(self) -> List[str]:
        """Get list of skill names."""
        return [skill.name for skill in self.skills]
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if agent has a specific skill."""
        return skill_name in self.get_skill_names()
