"""
User Data Transfer Object.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from src.domain.entities.user import User


@dataclass
class UserDTO:
    """
    DTO for user data sent to clients.
    """
    
    id: str
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: Optional[str]
    last_login_at: Optional[str]
    
    # Additional computed fields
    display_name: str = ""
    initials: str = ""
    
    # Preferences (limited exposure)
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_entity(cls, user: User, include_sensitive: bool = False) -> "UserDTO":
        """
        Create DTO from domain entity.
        """
        return cls(
            id=str(user.id),
            username=user.username,
            email=str(user.email) if include_sensitive else user.email.masked,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            bio=user.bio,
            created_at=user.created_at.isoformat() if user.created_at else None,
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
            display_name=user.display_name,
            initials=user.initials,
            preferences={
                k: v for k, v in user.preferences.items()
                if k in ["theme", "language", "notifications_enabled"]
            },
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "initials": self.initials,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at,
            "preferences": self.preferences,
        }