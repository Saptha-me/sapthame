"""A2A protocol response entity."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class A2AResponse:
    """Response from agent via A2A protocol."""
    
    content: str
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'A2AResponse':
        """Create A2AResponse from dictionary."""
        return cls(
            content=data.get('content', data.get('response', '')),
            success=data.get('success', True),
            error=data.get('error'),
            metadata=data.get('metadata', {})
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'content': self.content,
            'success': self.success,
            'error': self.error,
            'metadata': self.metadata
        }
