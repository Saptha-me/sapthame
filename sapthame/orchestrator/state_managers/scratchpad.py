"""Scratchpad manager for temporary notes and findings."""

from __future__ import annotations as _annotations

from typing import List, Optional


class ScratchpadManager:
    """Manages the scratchpad for temporary notes and findings.
    
    Provides a working memory for accumulating research findings, insights,
    and intermediate results during task execution.
    """
    
    def __init__(self, max_items: int = 50):
        """Initialize scratchpad manager.
        
        Args:
            max_items: Maximum number of items to keep. Older items are
                      removed when limit is exceeded. Default is 50.
        """
        self.content: List[str] = []
        self.max_items = max_items
        self._cached_content: Optional[str] = None
    
    def append(self, text: str) -> None:
        """Append text to scratchpad.
        
        Args:
            text: Text to append to the scratchpad.
        """
        if not text or not text.strip():
            return  # Skip empty entries
        
        self.content.append(text.strip())
        
        # Enforce max size by removing oldest items
        if len(self.content) > self.max_items:
            self.content = self.content[-self.max_items:]
        
        self._cached_content = None  # Invalidate cache
    
    def replace(self, text: str) -> None:
        """Replace entire scratchpad content.
        
        Args:
            text: New content to replace existing scratchpad.
        """
        self.content.clear()
        if text and text.strip():
            self.content.append(text.strip())
        self._cached_content = None  # Invalidate cache
    
    def clear(self) -> None:
        """Clear all scratchpad content."""
        self.content.clear()
        self._cached_content = None
    
    def is_empty(self) -> bool:
        """Check if scratchpad is empty.
        
        Returns:
            True if scratchpad has no content, False otherwise.
        """
        return len(self.content) == 0
    
    def get_item_count(self) -> int:
        """Get the number of items in scratchpad.
        
        Returns:
            Number of items currently stored.
        """
        return len(self.content)
    
    def get_content(self) -> str:
        """Get formatted scratchpad content with caching.
        
        Returns:
            Formatted string of all scratchpad items, or "(empty)" if empty.
        """
        if self.is_empty():
            return "(empty)"
        
        # Use cache if available
        if self._cached_content is not None:
            return self._cached_content
        
        # Build and cache content
        self._cached_content = "\n\n".join(self.content)
        return self._cached_content
    
    def to_prompt(self) -> str:
        """Format scratchpad for LLM prompt.
        
        Returns:
            Markdown-formatted scratchpad section for inclusion in prompts.
        """
        return f"## Scratchpad\n{self.get_content()}"
    
    def remove_item(self, index: int) -> bool:
        """Remove a specific item by index.
        
        Args:
            index: Zero-based index of item to remove.
            
        Returns:
            True if item was removed, False if index was invalid.
        """
        if 0 <= index < len(self.content):
            self.content.pop(index)
            self._cached_content = None
            return True
        return False
