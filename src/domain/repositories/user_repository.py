"""
Abstract user repository interface.
"""
from abc import abstractmethod
from typing import Optional, List
from uuid import UUID

from src.domain.entities.user import User
from src.domain.repositories.base_repository import BaseRepository
from src.shared.constants import UserRole


class IUserRepository(BaseRepository[User]):
    """
    Abstract interface for user repository.
    Defines user-specific data access methods.
    """
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Find user by email address."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Find user by username."""
        pass
    
    @abstractmethod
    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users."""
        pass
    
    @abstractmethod
    async def get_users_by_role(self, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """Get users by role."""
        pass
    
    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if email is already registered."""
        pass
    
    @abstractmethod
    async def username_exists(self, username: str) -> bool:
        """Check if username is already taken."""
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: UUID) -> None:
        """Update user's last login timestamp."""
        pass
    
    @abstractmethod
    async def update_password(self, user_id: UUID, hashed_password: str) -> None:
        """Update user's password."""
        pass
    
    @abstractmethod
    async def verify_email(self, user_id: UUID) -> None:
        """Mark user's email as verified."""
        pass
    
    @abstractmethod
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by username, email, or full name."""
        pass
    
    @abstractmethod
    async def get_user_stats(self, user_id: UUID) -> dict:
        """Get user statistics (conversation count, token usage, etc.)."""
        pass