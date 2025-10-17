"""Scratchpad manager for temporary notes and findings."""

from typing import List


class ScratchpadManager:
    """Manages the scratchpad for temporary notes and findings."""
    
    def __init__(self):
        self.content: List[str] = []
    
    def append(self, text: str):
        """Append text to scratchpad."""
        self.content.append(text)
    
    def replace(self, text: str):
        """Replace entire scratchpad content."""
        self.content = [text]
    
    def clear(self):
        """Clear scratchpad."""
        self.content = []
    
    def get_content(self) -> str:
        """Get formatted scratchpad content."""
        if not self.content:
            return "(empty)"
        return "\n\n".join(self.content)
    
    def to_prompt(self) -> str:
        """Format scratchpad for LLM prompt."""
        return f"## Scratchpad\n{self.get_content()}"
