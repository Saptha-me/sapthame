"""Phase execution result entity."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PhaseResult:
    """Result of executing all phases."""
    
    success: bool
    summary: str
    research_output: str
    plan_output: str
    implementation_output: str
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'summary': self.summary,
            'research_output': self.research_output,
            'plan_output': self.plan_output,
            'implementation_output': self.implementation_output,
            'error': self.error
        }
