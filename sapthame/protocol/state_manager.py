"""State manager for Bindu A2A protocol task tracking."""

import logging
from typing import Dict, List, Optional, Set
from datetime import datetime

from sapthame.protocol.entities.bindu_task import BinduTask, TaskState

logger = logging.getLogger(__name__)


class TaskStateManager:
    """Manages task state for Bindu A2A protocol communication."""
    
    def __init__(self):
        """Initialize task state manager."""
        self.tasks: Dict[str, BinduTask] = {}
        self.context_tasks: Dict[str, List[str]] = {}  # contextId -> [taskIds]
        self.active_tasks: Set[str] = set()  # Tasks in non-terminal states
        
    def add_task(self, task: BinduTask) -> None:
        """Add or update a task.
        
        Args:
            task: Task to add/update
        """
        task_id = task.taskId
        context_id = task.contextId
        
        # Update task
        self.tasks[task_id] = task
        
        # Track by context
        if context_id not in self.context_tasks:
            self.context_tasks[context_id] = []
        if task_id not in self.context_tasks[context_id]:
            self.context_tasks[context_id].append(task_id)
        
        # Track active state
        if task.is_terminal():
            self.active_tasks.discard(task_id)
        else:
            self.active_tasks.add(task_id)
        
        logger.debug(f"Task {task_id} added/updated with state: {task.state}")
    
    def get_task(self, task_id: str) -> Optional[BinduTask]:
        """Get task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        return self.tasks.get(task_id)
    
    def get_context_tasks(self, context_id: str) -> List[BinduTask]:
        """Get all tasks for a context.
        
        Args:
            context_id: Context ID
            
        Returns:
            List of tasks in the context
        """
        task_ids = self.context_tasks.get(context_id, [])
        return [self.tasks[tid] for tid in task_ids if tid in self.tasks]
    
    def get_active_tasks(self) -> List[BinduTask]:
        """Get all tasks in non-terminal states.
        
        Returns:
            List of active tasks
        """
        return [self.tasks[tid] for tid in self.active_tasks if tid in self.tasks]
    
    def get_completed_tasks(self) -> List[BinduTask]:
        """Get all completed tasks.
        
        Returns:
            List of completed tasks
        """
        return [task for task in self.tasks.values() if task.state == "completed"]
    
    def get_failed_tasks(self) -> List[BinduTask]:
        """Get all failed tasks.
        
        Returns:
            List of failed tasks
        """
        return [task for task in self.tasks.values() if task.state == "failed"]
    
    def update_task_state(
        self,
        task_id: str,
        state: TaskState,
        **kwargs
    ) -> bool:
        """Update task state and related fields.
        
        Args:
            task_id: Task ID
            state: New state
            **kwargs: Additional fields to update (prompt, error, etc.)
            
        Returns:
            True if updated, False if task not found
        """
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for state update")
            return False
        
        # Check if task is already terminal
        if task.is_terminal():
            logger.warning(f"Cannot update terminal task {task_id}")
            return False
        
        # Update state
        task.state = state
        task.updatedAt = datetime.utcnow().isoformat()
        
        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # Update active tracking
        if task.is_terminal():
            self.active_tasks.discard(task_id)
        
        logger.info(f"Task {task_id} state updated to: {state}")
        return True
    
    def is_context_complete(self, context_id: str) -> bool:
        """Check if all tasks in a context are in terminal states.
        
        Args:
            context_id: Context ID
            
        Returns:
            True if all tasks are terminal, False otherwise
        """
        tasks = self.get_context_tasks(context_id)
        if not tasks:
            return False
        return all(task.is_terminal() for task in tasks)
    
    def get_context_summary(self, context_id: str) -> Dict[str, int]:
        """Get summary of task states in a context.
        
        Args:
            context_id: Context ID
            
        Returns:
            Dictionary with state counts
        """
        tasks = self.get_context_tasks(context_id)
        summary = {
            "total": len(tasks),
            "submitted": 0,
            "working": 0,
            "input-required": 0,
            "auth-required": 0,
            "completed": 0,
            "failed": 0,
            "canceled": 0,
            "rejected": 0
        }
        
        for task in tasks:
            summary[task.state] += 1
        
        return summary
    
    def view_all(self) -> str:
        """Return formatted view of all tasks.
        
        Returns:
            Formatted string representation
        """
        if not self.tasks:
            return "No tasks tracked."
        
        lines = ["Task State Manager:"]
        lines.append(f"Total tasks: {len(self.tasks)}")
        lines.append(f"Active tasks: {len(self.active_tasks)}")
        lines.append("")
        
        # Group by context
        for context_id, task_ids in sorted(self.context_tasks.items()):
            lines.append(f"Context: {context_id}")
            summary = self.get_context_summary(context_id)
            lines.append(f"  Summary: {summary}")
            
            for task_id in task_ids:
                task = self.tasks.get(task_id)
                if task:
                    state_icon = self._get_state_icon(task.state)
                    lines.append(f"  {state_icon} [{task_id[:8]}...] {task.state}")
                    if task.messages:
                        last_msg = task.messages[-1]
                        preview = last_msg.content[:50] + "..." if len(last_msg.content) > 50 else last_msg.content
                        lines.append(f"      Last: {preview}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _get_state_icon(self, state: TaskState) -> str:
        """Get icon for task state.
        
        Args:
            state: Task state
            
        Returns:
            Icon string
        """
        icons = {
            "submitted": "📝",
            "working": "⚙️",
            "input-required": "❓",
            "auth-required": "🔐",
            "completed": "✅",
            "failed": "❌",
            "canceled": "🚫",
            "rejected": "⛔"
        }
        return icons.get(state, "•")
    
    def reset(self) -> None:
        """Reset the task state manager."""
        self.tasks.clear()
        self.context_tasks.clear()
        self.active_tasks.clear()
        logger.info("Task state manager reset")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "context_tasks": self.context_tasks,
            "active_tasks": list(self.active_tasks),
            "summary": {
                "total_tasks": len(self.tasks),
                "active_tasks": len(self.active_tasks),
                "contexts": len(self.context_tasks)
            }
        }
