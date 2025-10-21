"""Todo manager for tracking research tasks."""

from __future__ import annotations as _annotations

from typing import List, Optional

from sapthame.common.models import TodoItem


class TodoManager:
    """Manages the todo list for tracking research tasks.
    
    Provides task tracking with completion status, automatic size limits,
    and efficient caching for prompt generation.
    """
    
    def __init__(self, max_items: int = 100):
        """Initialize todo manager.
        
        Args:
            max_items: Maximum number of items to keep. Older items are
                      removed when limit is exceeded. Default is 100.
        """
        self.items: List[TodoItem] = []
        self.max_items = max_items
        self._cached_status: Optional[str] = None
    
    def add_item(self, item: str) -> bool:
        """Add a new todo item.
        
        Args:
            item: Text description of the todo item.
            
        Returns:
            True if item was added, False if item was empty/invalid.
        """
        if not item or not item.strip():
            return False
        
        self.items.append(TodoItem(text=item.strip()))
        
        # Enforce max size by removing oldest completed items first,
        # then oldest items if still over limit
        if len(self.items) > self.max_items:
            self._prune_items()
        
        self._cached_status = None  # Invalidate cache
        return True
    
    def _prune_items(self) -> None:
        """Remove oldest items to stay within max_items limit.
        
        Prioritizes removing completed items first.
        """
        # First, try removing completed items
        if any(item.completed for item in self.items):
            self.items = [item for item in self.items if not item.completed]
        
        # If still over limit, remove oldest items
        if len(self.items) > self.max_items:
            self.items = self.items[-self.max_items:]
    
    def complete_item(self, index: int) -> bool:
        """Mark a todo item as completed.
        
        Args:
            index: Zero-based index of item to complete.
            
        Returns:
            True if item was completed, False if index was invalid.
        """
        if 0 <= index < len(self.items):
            self.items[index].completed = True
            self._cached_status = None
            return True
        return False
    
    def uncomplete_item(self, index: int) -> bool:
        """Mark a todo item as not completed.
        
        Args:
            index: Zero-based index of item to uncomplete.
            
        Returns:
            True if item was uncompleted, False if index was invalid.
        """
        if 0 <= index < len(self.items):
            self.items[index].completed = False
            self._cached_status = None
            return True
        return False
    
    def remove_item(self, index: int) -> bool:
        """Remove a todo item.
        
        Args:
            index: Zero-based index of item to remove.
            
        Returns:
            True if item was removed, False if index was invalid.
        """
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self._cached_status = None
            return True
        return False
    
    def clear_completed(self) -> int:
        """Remove all completed items.
        
        Returns:
            Number of items removed.
        """
        initial_count = len(self.items)
        self.items = [item for item in self.items if not item.completed]
        removed_count = initial_count - len(self.items)
        
        if removed_count > 0:
            self._cached_status = None
        
        return removed_count
    
    def clear_all(self) -> None:
        """Remove all items from the todo list."""
        self.items.clear()
        self._cached_status = None
    
    def is_empty(self) -> bool:
        """Check if todo list is empty.
        
        Returns:
            True if no items exist, False otherwise.
        """
        return len(self.items) == 0
    
    def get_item_count(self) -> int:
        """Get total number of items.
        
        Returns:
            Total number of todo items.
        """
        return len(self.items)
    
    def get_pending_count(self) -> int:
        """Get count of pending (not completed) items.
        
        Returns:
            Number of items not yet completed.
        """
        return sum(1 for item in self.items if not item.completed)
    
    def get_completed_count(self) -> int:
        """Get count of completed items.
        
        Returns:
            Number of completed items.
        """
        return sum(1 for item in self.items if item.completed)
    
    def get_status(self) -> str:
        """Get formatted todo list status with caching.
        
        Returns:
            Formatted string of all todo items with status indicators,
            or "(no items)" if empty.
        """
        if self.is_empty():
            return "(no items)"
        
        # Use cache if available
        if self._cached_status is not None:
            return self._cached_status
        
        # Build status using list comprehension for efficiency
        lines = [
            f"{i}. {item}"
            for i, item in enumerate(self.items)
        ]
        
        self._cached_status = "\n".join(lines)
        return self._cached_status
    
    def to_prompt(self) -> str:
        """Format todo list for LLM prompt.
        
        Returns:
            Markdown-formatted todo list section for inclusion in prompts.
        """
        status = self.get_status()
        pending = self.get_pending_count()
        total = self.get_item_count()
        
        return f"## Todo List ({pending}/{total} pending)\n{status}"
