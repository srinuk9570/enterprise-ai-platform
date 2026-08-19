"""
Command for updating user information.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.commands.base_command import BaseCommand


@dataclass
class UpdateUserCommand(BaseCommand):
    """
    Command to update user profile.
    """
    
    user_id: UUID
    updated_by: UUID  # User performing the update (for permissions)
    
    # Updatable fields
    full_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Role management (requires admin)
    new_role: Optional[str] = None
    
    # Preferences
    preferences: Optional[dict] = None
    
    # Password change
    current_password: Optional[str] = None
    new_password: Optional[str] = None
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate command data."""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.updated_by:
            errors.append("Updated by user ID is required")
        
        if self.email and "@" not in self.email:
            errors.append("Invalid email format")
        
        if self.full_name is not None and len(self.full_name) > 100:
            errors.append("Full name must be at most 100 characters")
        
        if self.bio is not None and len(self.bio) > 500:
            errors.append("Bio must be at most 500 characters")
        
        if self.new_password:
            if not self.current_password:
                errors.append("Current password is required to change password")
            if len(self.new_password) < 8:
                errors.append("New password must be at least 8 characters")
        
        if self.new_role and self.new_role not in ["admin", "power_user", "user", "viewer"]:
            errors.append(f"Invalid role: {self.new_role}")
        
        return len(errors) == 0, errors
    
    def has_profile_updates(self) -> bool:
        """Check if there are profile updates."""
        return any([
            self.full_name is not None,
            self.email is not None,
            self.bio is not None,
            self.avatar_url is not None,
            self.preferences is not None,
        ])
    
    def has_password_change(self) -> bool:
        """Check if password is being changed."""
        return self.current_password is not None and self.new_password is not None
    
    def has_role_change(self) -> bool:
        """Check if role is being changed."""
        return self.new_role is not None