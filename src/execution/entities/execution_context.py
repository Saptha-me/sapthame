"""Execution context passed between phases."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ExecutionContext:
    """Context passed between phases during execution."""
    
    query: str
    research_summary: Optional[str] = None
    execution_plan: Optional[str] = None
    implementation_results: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'query': self.query,
            'research_summary': self.research_summary,
            'execution_plan': self.execution_plan,
            'implementation_results': self.implementation_results,
            'metadata': self.metadata
        }
