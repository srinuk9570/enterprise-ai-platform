"""
Base command class for CQRS pattern.
"""
from abc import ABC
from typing import Optional


class BaseCommand(ABC):
    """
    Base class for all commands.
    Commands represent an intent to change state.
    """
    
    def __init__(
        self,
        command_id: Optional[str] = None,
        timestamp: Optional[object] = None,
        initiated_by: Optional[str] = None,
        correlation_id: Optional[str] = None,
        source: str = "api",
    ):
        from datetime import datetime
        from uuid import uuid4
        
        self.command_id = command_id or str(uuid4())
        self.timestamp = timestamp or datetime.utcnow()
        self.initiated_by = initiated_by
        self.correlation_id = correlation_id
        self.source = source
    
    def to_dict(self) -> dict:
        """Convert command to dictionary for logging/serialization."""
        return {
            "command_type": self.__class__.__name__,
            "command_id": str(self.command_id),
            "timestamp": self.timestamp.isoformat(),
            "initiated_by": str(self.initiated_by) if self.initiated_by else None,
            "correlation_id": self.correlation_id,
            "source": self.source,
        }