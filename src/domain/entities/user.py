"""
User domain entity with business rules and validation.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4

from src.shared.constants import UserRole
from src.domain.exceptions import DomainValidationError, UnauthorizedOperationError
from src.domain.value_objects.email import Email


@dataclass
class User:
    """User aggregate root."""
    
    email: Email
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_verified: bool = False
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    preferences: dict = field(default_factory=dict)
    
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    email_verified_at: Optional[datetime] = None
    
    conversations: List = field(default_factory=list, repr=False)
    assets: List = field(default_factory=list, repr=False)
    
    def __post_init__(self) -> None:
        self._validate_username()
        self._validate_bio()
    
    def _validate_username(self) -> None:
        if not self.username:
            raise DomainValidationError("Username cannot be empty")
        if len(self.username) < 3:
            raise DomainValidationError("Username must be at least 3 characters")
        if len(self.username) > 50:
            raise DomainValidationError("Username must be at most 50 characters")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if not all(c in allowed for c in self.username):
            raise DomainValidationError("Username contains invalid characters")
        if self.username[0] in "-_" or self.username[-1] in "-_":
            raise DomainValidationError("Username cannot start/end with hyphen or underscore")
    
    def _validate_bio(self) -> None:
        if self.bio and len(self.bio) > 500:
            raise DomainValidationError("Bio must be at most 500 characters")
    
    def change_password(self, new_hashed_password: str) -> None:
        if not new_hashed_password:
            raise DomainValidationError("Password cannot be empty")
        self.hashed_password = new_hashed_password
        self.updated_at = datetime.utcnow()
    
    def update_profile(
        self,
        full_name: Optional[str] = None,
        email: Optional[Email] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> None:
        if full_name is not None:
            if len(full_name) > 100:
                raise DomainValidationError("Full name must be at most 100 characters")
            self.full_name = full_name if full_name.strip() else None
        if email is not None:
            self.email = email
            self.is_verified = False
            self.email_verified_at = None
        if bio is not None:
            self.bio = bio
            self._validate_bio()
        if avatar_url is not None:
            if avatar_url and len(avatar_url) > 500:
                raise DomainValidationError("Avatar URL must be at most 500 characters")
            self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()
    
    def update_preferences(self, preferences: dict) -> None:
        self.preferences = {**self.preferences, **preferences}
        self.updated_at = datetime.utcnow()
    
    def record_login(self) -> None:
        if not self.is_active:
            raise DomainValidationError("Cannot login with deactivated account")
        self.last_login_at = datetime.utcnow()
    
    def deactivate(self) -> None:
        if not self.is_active:
            raise DomainValidationError("User is already deactivated")
        self.is_active = False
        self.updated_at = datetime.utcnow()
    
    def activate(self) -> None:
        if self.is_active:
            raise DomainValidationError("User is already active")
        self.is_active = True
        self.updated_at = datetime.utcnow()
    
    def verify_email(self) -> None:
        if self.is_verified:
            raise DomainValidationError("Email is already verified")
        self.is_verified = True
        self.email_verified_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def promote_to_role(self, new_role: UserRole, promoted_by: Optional['User'] = None) -> None:
        hierarchy = {UserRole.VIEWER: 0, UserRole.USER: 1, UserRole.POWER_USER: 2, UserRole.ADMIN: 3}
        current = hierarchy.get(self.role, 0)
        new = hierarchy.get(new_role, 0)
        if promoted_by:
            promoter = hierarchy.get(promoted_by.role, 0)
            if promoter <= current:
                raise UnauthorizedOperationError("Cannot modify user with equal or higher role")
        if new <= current:
            raise DomainValidationError(f"Cannot demote from {self.role.value} to {new_role.value}")
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def demote_to_role(self, new_role: UserRole, demoted_by: 'User') -> None:
        if demoted_by.role != UserRole.ADMIN:
            raise UnauthorizedOperationError("Only admins can demote users")
        hierarchy = {UserRole.VIEWER: 0, UserRole.USER: 1, UserRole.POWER_USER: 2, UserRole.ADMIN: 3}
        current = hierarchy.get(self.role, 0)
        new = hierarchy.get(new_role, 0)
        if new >= current:
            raise DomainValidationError(f"Cannot promote using demote method")
        if self.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
            raise DomainValidationError("Cannot demote admin user")
        self.role = new_role
        self.updated_at = datetime.utcnow()
    
    def has_permission(self, required_role: UserRole) -> bool:
        hierarchy = {UserRole.VIEWER: 0, UserRole.USER: 1, UserRole.POWER_USER: 2, UserRole.ADMIN: 3}
        return hierarchy.get(self.role, 0) >= hierarchy.get(required_role, 0)
    
    def can_access_resource(self, resource_owner_id: UUID) -> bool:
        return self.id == resource_owner_id or self.role == UserRole.ADMIN
    
    def can_modify_resource(self, resource_owner_id: UUID) -> bool:
        return self.id == resource_owner_id or self.role == UserRole.ADMIN
    
    def get_conversation_limit(self) -> int:
        """Get maximum conversations allowed based on role."""
        limits = {
            UserRole.VIEWER: 10,
            UserRole.USER: 50,
            UserRole.POWER_USER: 200,
            UserRole.ADMIN: 1000,
        }
        return limits.get(self.role, 50)
    
    def get_daily_token_limit(self) -> int:
        """Get daily token limit based on role."""
        limits = {
            UserRole.VIEWER: 10000,
            UserRole.USER: 50000,
            UserRole.POWER_USER: 200000,
            UserRole.ADMIN: 1000000,
        }
        return limits.get(self.role, 50000)
    
    @property
    def display_name(self) -> str:
        return self.full_name or self.username
    
    @property
    def initials(self) -> str:
        name = self.display_name
        parts = name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return name[:2].upper()
    
    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    @property
    def is_power_user(self) -> bool:
        return self.role in [UserRole.POWER_USER, UserRole.ADMIN]
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        return {
            "id": str(self.id),
            "email": self.email.masked if not include_sensitive else str(self.email),
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role.value,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }