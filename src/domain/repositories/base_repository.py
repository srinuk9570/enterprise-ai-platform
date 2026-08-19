"""
Abstract base repository interface.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from uuid import UUID

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository defining standard CRUD operations.
    All concrete repositories must implement these methods.
    """
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Retrieve entity by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination."""
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete an entity by ID."""
        pass
    
    @abstractmethod
    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total count of entities."""
        pass