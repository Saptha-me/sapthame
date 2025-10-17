"""Bindu protocol task entities following A2A Task-First pattern."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime


TaskState = Literal[
    "submitted",      # Initial state
    "working",        # Agent processing
    "input-required", # Waiting for user input
    "auth-required",  # Waiting for authentication
    "completed",      # Success with artifacts
    "failed",         # Error occurred
    "canceled",       # User canceled
    "rejected"        # Agent rejected
]


@dataclass
class Artifact:
    """Task artifact (output/deliverable)."""
    
    artifactId: str
    taskId: str
    mimeType: str
    data: str  # Base64 encoded or JSON string
    signature: Optional[str] = None  # DID signature
    createdAt: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "artifactId": self.artifactId,
            "taskId": self.taskId,
            "mimeType": self.mimeType,
            "data": self.data,
            "createdAt": self.createdAt
        }
        if self.signature:
            result["signature"] = self.signature
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artifact":
        """Create from dictionary."""
        return cls(
            artifactId=data["artifactId"],
            taskId=data["taskId"],
            mimeType=data["mimeType"],
            data=data["data"],
            signature=data.get("signature"),
            createdAt=data.get("createdAt", datetime.utcnow().isoformat())
        )


@dataclass
class TaskMessage:
    """Message within a task."""
    
    messageId: str
    role: Literal["user", "assistant"]
    content: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "messageId": self.messageId,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskMessage":
        """Create from dictionary."""
        return cls(
            messageId=data["messageId"],
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.utcnow().isoformat())
        )


@dataclass
class BinduTask:
    """Task following Bindu A2A protocol."""
    
    taskId: str
    contextId: str
    state: TaskState
    messages: List[TaskMessage] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    referenceTaskIds: List[str] = field(default_factory=list)
    createdAt: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updatedAt: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    prompt: Optional[str] = None  # For input-required or auth-required states
    authType: Optional[str] = None  # For auth-required state
    service: Optional[str] = None  # For auth-required state
    error: Optional[str] = None  # For failed state
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "taskId": self.taskId,
            "contextId": self.contextId,
            "state": self.state,
            "messages": [msg.to_dict() for msg in self.messages],
            "artifacts": [art.to_dict() for art in self.artifacts],
            "referenceTaskIds": self.referenceTaskIds,
            "createdAt": self.createdAt,
            "updatedAt": self.updatedAt
        }
        if self.prompt:
            result["prompt"] = self.prompt
        if self.authType:
            result["authType"] = self.authType
        if self.service:
            result["service"] = self.service
        if self.error:
            result["error"] = self.error
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BinduTask":
        """Create from dictionary."""
        return cls(
            taskId=data["taskId"],
            contextId=data["contextId"],
            state=data["state"],
            messages=[TaskMessage.from_dict(m) for m in data.get("messages", [])],
            artifacts=[Artifact.from_dict(a) for a in data.get("artifacts", [])],
            referenceTaskIds=data.get("referenceTaskIds", []),
            createdAt=data.get("createdAt", datetime.utcnow().isoformat()),
            updatedAt=data.get("updatedAt", datetime.utcnow().isoformat()),
            prompt=data.get("prompt"),
            authType=data.get("authType"),
            service=data.get("service"),
            error=data.get("error")
        )
    
    def is_terminal(self) -> bool:
        """Check if task is in terminal state (immutable)."""
        return self.state in ["completed", "failed", "canceled", "rejected"]
    
    def is_working(self) -> bool:
        """Check if task is being processed."""
        return self.state in ["submitted", "working"]
    
    def needs_input(self) -> bool:
        """Check if task needs user input."""
        return self.state in ["input-required", "auth-required"]
