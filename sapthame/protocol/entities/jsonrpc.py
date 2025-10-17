"""JSON-RPC 2.0 protocol entities."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from uuid import uuid4


@dataclass
class JSONRPCRequest:
    """JSON-RPC 2.0 request."""
    
    method: str
    params: Dict[str, Any]
    jsonrpc: str = "2.0"
    id: str = None
    
    def __post_init__(self):
        """Generate ID if not provided."""
        if self.id is None:
            self.id = str(uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "params": self.params,
            "id": self.id
        }


@dataclass
class JSONRPCError:
    """JSON-RPC 2.0 error."""
    
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONRPCError":
        """Create from dictionary."""
        return cls(
            code=data["code"],
            message=data["message"],
            data=data.get("data")
        )


@dataclass
class JSONRPCResponse:
    """JSON-RPC 2.0 response."""
    
    id: str
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        response = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error:
            response["error"] = self.error.to_dict()
        else:
            response["result"] = self.result
        return response
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JSONRPCResponse":
        """Create from dictionary."""
        error = None
        if "error" in data:
            error = JSONRPCError.from_dict(data["error"])
        
        return cls(
            id=data["id"],
            jsonrpc=data.get("jsonrpc", "2.0"),
            result=data.get("result"),
            error=error
        )
    
    def is_success(self) -> bool:
        """Check if response is successful."""
        return self.error is None
