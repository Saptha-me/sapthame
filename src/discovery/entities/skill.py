"""Skill entity for agent capabilities."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Skill:
    """Represents a skill that an agent possesses."""
    
    name: str
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Skill':
        """Create Skill from dictionary."""
        return cls(
            name=data['name'],
            description=data['description']
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description
        }
