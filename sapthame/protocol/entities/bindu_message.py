"""Bindu protocol message entities following A2A Task-First pattern."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal
from uuid import uuid4


@dataclass
class MessagePart:
    """Part of a message (text, image, etc.)."""
    
    kind: Literal["text", "image", "file"]
    text: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded for binary data
    mimeType: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"kind": self.kind}
        if self.text is not None:
            result["text"] = self.text
        if self.data is not None:
            result["data"] = self.data
        if self.mimeType is not None:
            result["mimeType"] = self.mimeType
        return result


@dataclass
class BinduMessage:
    """Message following Bindu A2A protocol."""
    
    role: Literal["user", "assistant"]
    parts: List[MessagePart]
    kind: Literal["message"] = "message"
    messageId: str = field(default_factory=lambda: str(uuid4()))
    contextId: str = field(default_factory=lambda: str(uuid4()))
    taskId: str = field(default_factory=lambda: str(uuid4()))
    referenceTaskIds: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "role": self.role,
            "parts": [part.to_dict() for part in self.parts],
            "kind": self.kind,
            "messageId": self.messageId,
            "contextId": self.contextId,
            "taskId": self.taskId,
            "referenceTaskIds": self.referenceTaskIds
        }
    
    @classmethod
    def create_text_message(
        cls,
        text: str,
        context_id: Optional[str] = None,
        task_id: Optional[str] = None,
        reference_task_ids: Optional[List[str]] = None
    ) -> "BinduMessage":
        """Create a simple text message."""
        msg = cls(
            role="user",
            parts=[MessagePart(kind="text", text=text)]
        )
        if context_id:
            msg.contextId = context_id
        if task_id:
            msg.taskId = task_id
        if reference_task_ids:
            msg.referenceTaskIds = reference_task_ids
        return msg


@dataclass
class MessageConfiguration:
    """Configuration for message sending."""
    
    acceptedOutputModes: List[str] = field(default_factory=lambda: ["application/json"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "acceptedOutputModes": self.acceptedOutputModes
        }
