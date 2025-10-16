"""A2A protocol message entity."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class A2AMessage:
    """Message sent to agent via A2A protocol."""
    
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'message': self.message,
            'context': self.context
        }
