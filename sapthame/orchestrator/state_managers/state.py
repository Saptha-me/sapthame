"""State management for Saptami orchestrator."""

from __future__ import annotations as _annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from enum import Enum

from sapthame.discovery.agent_registry import AgentRegistry
from sapthame.orchestrator.state_managers.conversation_history import ConversationHistory
from sapthame.common.models import Phase

@dataclass
class State:
    """Orchestrator state tracking execution progress.
    
    Manages the complete execution state including phase tracking,
    outputs, and completion status with efficient caching.
    """
    
    agent_registry: AgentRegistry
    conversation_history: ConversationHistory
    
    # Query
    query: Optional[str] = None
    
    # Phase tracking
    current_phase: Phase = Phase.RESEARCH
    research_output: Optional[str] = None
    plan_output: Optional[str] = None
    implementation_output: Optional[str] = None
    
    # Execution state
    done: bool = False
    finish_message: Optional[str] = None
    
    # Additional context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Cache fields
    _cached_dict: Optional[Dict[str, Any]] = field(default=None, init=False, repr=False)
    _cached_prompt: Optional[str] = field(default=None, init=False, repr=False)
    
    def _invalidate_cache(self) -> None:
        """Invalidate all cached values."""
        self._cached_dict = None
        self._cached_prompt = None
    
    def set_phase(self, phase: Phase) -> None:
        """Set the current execution phase.
        
        Args:
            phase: Phase name (research, planning, or implementation).
        """
        if phase != self.current_phase:
            self.current_phase = phase
            self._invalidate_cache()
    
    def set_research_output(self, output: str) -> None:
        """Set research phase output.
        
        Args:
            output: Research findings and results.
        """
        self.research_output = output
        self._invalidate_cache()
    
    def set_plan_output(self, output: str) -> None:
        """Set planning phase output.
        
        Args:
            output: Planning results and strategy.
        """
        self.plan_output = output
        self._invalidate_cache()
    
    def set_implementation_output(self, output: str) -> None:
        """Set implementation phase output.
        
        Args:
            output: Implementation results.
        """
        self.implementation_output = output
        self._invalidate_cache()
    
    def mark_done(self, message: str) -> None:
        """Mark execution as complete.
        
        Args:
            message: Completion message.
        """
        self.done = True
        self.finish_message = message
        self._invalidate_cache()
    
    def reset(self) -> None:
        """Reset state to initial values."""
        self.query = None
        self.current_phase = Phase.RESEARCH
        self.research_output = None
        self.plan_output = None
        self.implementation_output = None
        self.done = False
        self.finish_message = None
        self.metadata.clear()
        self._invalidate_cache()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary with caching.
        
        Returns:
            Dictionary representation of state.
        """
        # Use cache if available
        if self._cached_dict is not None:
            return self._cached_dict
        
        # Build dict
        self._cached_dict = {
            "current_phase": self.current_phase,
            "research_output": self.research_output,
            "plan_output": self.plan_output,
            "implementation_output": self.implementation_output,
            "done": self.done,
            "finish_message": self.finish_message,
            "metadata": self.metadata,
            "agents": [agent.to_dict() for agent in self.agent_registry.agents.values()],
        }
        
        return self._cached_dict
    
    def to_prompt(self, max_output_length: Optional[int] = None) -> str:
        """Generate prompt representation of current state with caching.
        
        Args:
            max_output_length: Optional max length for each output section.
                              Useful for limiting context size.
        
        Returns:
            Formatted string for LLM context.
        """
        # Use cache if available and no truncation requested
        if max_output_length is None and self._cached_prompt is not None:
            return self._cached_prompt
        
        # Build sections using list comprehension for efficiency
        sections = [f"## Current Phase: {self.current_phase}"]
        
        # Helper to truncate if needed
        def maybe_truncate(text: str) -> str:
            if max_output_length and len(text) > max_output_length:
                return text[:max_output_length] + "..."
            return text
        
        if self.research_output:
            output = maybe_truncate(self.research_output)
            sections.append(f"## Research Output\n{output}")
        
        if self.plan_output:
            output = maybe_truncate(self.plan_output)
            sections.append(f"## Plan Output\n{output}")
        
        if self.implementation_output:
            output = maybe_truncate(self.implementation_output)
            sections.append(f"## Implementation Output\n{output}")
        
        if self.metadata:
            sections.append(f"## Metadata\n{self.metadata}")
        
        result = "\n\n".join(sections)
        
        # Cache if no truncation
        if max_output_length is None:
            self._cached_prompt = result
        
        return result
    
    def get_phase_progress(self) -> Dict[str, bool]:
        """Get completion status of each phase.
        
        Returns:
            Dictionary mapping phase names to completion status.
        """
        return {
            "research": self.research_output is not None,
            "planning": self.plan_output is not None,
            "implementation": self.implementation_output is not None,
        }
    
    def is_phase_complete(self, phase: str) -> bool:
        """Check if a specific phase is complete.
        
        Args:
            phase: Phase name to check.
            
        Returns:
            True if phase has output, False otherwise.
        """
        phase_outputs = {
            "research": self.research_output,
            "planning": self.plan_output,
            "implementation": self.implementation_output,
        }
        return phase_outputs.get(phase) is not None
