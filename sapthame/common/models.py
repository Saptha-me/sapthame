"""Common data models for Saptami."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Skill:
    """Agent skill definition."""
    name: str
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Create Skill from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description
        }


@dataclass
class AgentInfo:
    """Agent information from get-info.json."""
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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInfo":
        """Create AgentInfo from dictionary."""
        skills = [Skill.from_dict(s) for s in data.get("skills", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            url=data["url"],
            version=data["version"],
            protocol_version=data.get("protocolVersion", "1.0"),
            skills=skills,
            capabilities=data.get("capabilities", {}),
            extra_data=data.get("extraData", {}),
            agent_trust=data.get("agentTrust", "medium")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "protocolVersion": self.protocol_version,
            "skills": [s.to_dict() for s in self.skills],
            "capabilities": self.capabilities,
            "extraData": self.extra_data,
            "agentTrust": self.agent_trust
        }
    
    def get_skill_names(self) -> List[str]:
        """Get list of skill names."""
        return [skill.name for skill in self.skills]


@dataclass
class PhaseResult:
    """Result of executing a phase."""
    success: bool
    summary: str
    research_output: Optional[str] = None
    plan_output: Optional[str] = None
    implementation_output: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert phase result to dictionary format."""
        return {
            "success": self.success,
            "summary": self.summary,
            "research_output": self.research_output,
            "plan_output": self.plan_output,
            "implementation_output": self.implementation_output,
            "error": self.error
        }