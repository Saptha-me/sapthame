"""Conversation history manager for tracking interactions."""

from __future__ import annotations as _annotations

from typing import List, Optional
from dataclasses import dataclass, field
from collections import deque

from sapthame.orchestrator.turn import Turn


@dataclass
class ConversationHistory:
    """Manages conversation history for state tracking."""
    max_turns: int = 100
    turns: deque = field(default=None, init=False, repr=False)
    _cached_prompt: Optional[str] = field(default=None, init=False, repr=False)
    
    def __post_init__(self):
        """Initialize deque with max_turns after dataclass initialization."""
        self.turns = deque(maxlen=self.max_turns)
    
    def add_turn(self, turn: Turn):
        """Add a turn to history, maintaining max size."""
        self.turns.append(turn)
        self._cached_prompt = None  # Invalidate cache
    
    def to_prompt(self, max_recent_turns: Optional[int] = None) -> str:
        """Convert history to prompt format with optional recent turn limit.
        
        Args:
            max_recent_turns: If set, only include the N most recent turns.
                             Useful for limiting context size in prompts.
        
        Returns:
            Formatted conversation history string.
        """
        if not self.turns:
            return "No previous interactions."
        
        # Use cache if available and no limit specified
        if max_recent_turns is None and self._cached_prompt is not None:
            return self._cached_prompt
        
        # Select turns to include
        turns_to_include = list(self.turns)
        if max_recent_turns is not None and len(turns_to_include) > max_recent_turns:
            turns_to_include = turns_to_include[-max_recent_turns:]
        
        # Build prompt using list comprehension for efficiency
        turn_strs = [
            f"--- Turn {i} ---\n{turn.to_prompt()}"
            for i, turn in enumerate(turns_to_include, 1)
        ]
        
        result = "\n\n".join(turn_strs)
        
        # Cache if full history
        if max_recent_turns is None:
            self._cached_prompt = result
        
        return result


    def to_dict(self) -> List[dict]:
        """Convert history to a list of dicts for structured logging.
        
        Returns:
            List of turn dictionaries in chronological order.
        """
        return [turn.to_dict() for turn in self.turns]
    
    def get_turn_count(self) -> int:
        """Get the current number of turns in history."""
        return len(self.turns)
    
    def clear(self) -> None:
        """Clear all conversation history."""
        self.turns.clear()
        self._cached_prompt = None
