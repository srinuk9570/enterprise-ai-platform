"""
Abstract asset repository interface.
"""
from abc import abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.generated_asset import GeneratedAsset
from src.domain.repositories.base_repository import BaseRepository
from src.shared.constants import AssetType


class IAssetRepository(BaseRepository[GeneratedAsset]):
    """
    Abstract interface for asset repository.
    """
    
    @abstractmethod
    async def get_by_user_id(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        asset_type: Optional[AssetType] = None,
    ) -> List[GeneratedAsset]:
        """Get all assets for a user."""
        pass
    
    @abstractmethod
    async def get_by_type(
        self,
        user_id: UUID,
        asset_type: AssetType,
        skip: int = 0,
        limit: int = 100,
    ) -> List[GeneratedAsset]:
        """Get assets by type."""
        pass
    
    @abstractmethod
    async def get_favorites(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> List[GeneratedAsset]:
        """Get user's favorite assets."""
        pass
    
    @abstractmethod
    async def get_recent_assets(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> List[GeneratedAsset]:
        """Get user's most recent assets."""
        pass
    
    @abstractmethod
    async def search_assets(
        self,
        user_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[GeneratedAsset]:
        """Search user's assets by title, description, or prompt."""
        pass
    
    @abstractmethod
    async def get_by_conversation(
        self,
        conversation_id: UUID,
    ) -> List[GeneratedAsset]:
        """Get assets generated in a specific conversation."""
        pass
    
    @abstractmethod
    async def get_public_assets(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> List[GeneratedAsset]:
        """Get public assets from all users."""
        pass
    
    @abstractmethod
    async def increment_view_count(self, asset_id: UUID) -> None:
        """Increment asset view count."""
        pass
    
    @abstractmethod
    async def increment_download_count(self, asset_id: UUID) -> None:
        """Increment asset download count."""
        pass
    
    @abstractmethod
    async def get_storage_stats(self, user_id: UUID) -> dict:
        """Get storage statistics for user."""
        pass
    
    @abstractmethod
    async def delete_old_assets(
        self,
        user_id: UUID,
        days_old: int = 30,
        keep_favorites: bool = True,
    ) -> int:
        """Delete assets older than specified days."""
        pass
    
    @abstractmethod
    async def get_total_size(self, user_id: UUID) -> int:
        """Get total size of user's assets in bytes."""
        pass
    
    @abstractmethod
    async def get_by_tag(
        self,
        user_id: UUID,
        tag: str,
        limit: int = 50,
    ) -> List[GeneratedAsset]:
        """Get assets by tag."""
        pass