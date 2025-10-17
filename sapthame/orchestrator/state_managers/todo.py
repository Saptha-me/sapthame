"""Todo manager for tracking research tasks."""

from typing import List, Dict, Any


class TodoManager:
    """Manages the todo list for tracking research tasks."""
    
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
    
    def add_item(self, item: str):
        """Add a new todo item."""
        self.items.append({
            "text": item,
            "completed": False
        })
    
    def complete_item(self, index: int):
        """Mark a todo item as completed."""
        if 0 <= index < len(self.items):
            self.items[index]["completed"] = True
    
    def remove_item(self, index: int):
        """Remove a todo item."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
    
    def get_status(self) -> str:
        """Get formatted todo list status."""
        if not self.items:
            return "(no items)"
        
        lines = []
        for i, item in enumerate(self.items):
            status = "✓" if item["completed"] else "○"
            lines.append(f"{i}. {status} {item['text']}")
        
        return "\n".join(lines)
    
    def to_prompt(self) -> str:
        """Format todo list for LLM prompt."""
        return f"## Todo List\n{self.get_status()}"
    
    def get_pending_count(self) -> int:
        """Get count of pending items."""
        return sum(1 for item in self.items if not item["completed"])
