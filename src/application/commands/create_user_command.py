"""
Command for creating a new user.
"""
from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4
from datetime import datetime

from src.application.commands.base_command import BaseCommand


@dataclass
class CreateUserCommand:
    """
    Command to create a new user account.
    """
    
    email: str
    username: str
    password: str
    
    # Optional fields with defaults
    full_name: Optional[str] = None
    role: str = "user"
    send_verification_email: bool = True
    auto_verify: bool = False
    
    # Command metadata (from BaseCommand, copied here)
    command_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    initiated_by: Optional[str] = None
    correlation_id: Optional[str] = None
    source: str = "api"
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate command data before processing.
        Returns (is_valid, list_of_errors).
        """
        errors = []
        
        if not self.email or "@" not in self.email:
            errors.append("Valid email is required")
        
        if not self.username or len(self.username) < 3:
            errors.append("Username must be at least 3 characters")
        
        if not self.password or len(self.password) < 8:
            errors.append("Password must be at least 8 characters")
        
        if self.role not in ["admin", "power_user", "user", "viewer"]:
            errors.append(f"Invalid role: {self.role}")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> dict:
        """Convert command to dictionary for logging/serialization."""
        return {
            "command_type": self.__class__.__name__,
            "command_id": self.command_id,
            "timestamp": self.timestamp.isoformat(),
            "initiated_by": self.initiated_by,
            "correlation_id": self.correlation_id,
            "source": self.source,
        }