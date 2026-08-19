"""
Asset Data Transfer Object.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from src.domain.entities.generated_asset import GeneratedAsset


@dataclass
class AssetDTO:
    """
    DTO for asset data sent to clients.
    """
    
    id: str
    user_id: str
    asset_type: str
    file_name: str
    file_size: int
    formatted_file_size: str
    mime_type: str
    created_at: str
    
    # ADDED: File path for server-side operations
    file_path: Optional[str] = None
    
    # Optional fields
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    model_used: Optional[str] = None
    generation_time_ms: Optional[float] = None
    
    # Generation parameters
    generation_params: Optional[Dict[str, Any]] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    is_favorite: bool = False
    is_public: bool = False
    view_count: int = 0
    download_count: int = 0
    
    # Relations
    conversation_id: Optional[str] = None
    chart_configuration_id: Optional[str] = None
    
    # URLs
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    @classmethod
    def from_entity(cls, asset: GeneratedAsset) -> "AssetDTO":
        """
        Create DTO from domain entity.
        
        Args:
            asset: GeneratedAsset domain entity
            
        Returns:
            AssetDTO instance with all fields populated
        """
        # Truncate prompt if it's too long for display
        truncated_prompt = asset.prompt
        if asset.prompt and len(asset.prompt) > 200:
            truncated_prompt = asset.prompt[:197] + "..."
        
        return cls(
            id=str(asset.id),
            user_id=str(asset.user_id),
            asset_type=asset.asset_type.value if hasattr(asset.asset_type, 'value') else str(asset.asset_type),
            file_name=asset.file_name,
            file_size=asset.file_size,
            formatted_file_size=asset.formatted_file_size,
            mime_type=asset.mime_type,
            created_at=asset.created_at.isoformat() if asset.created_at else "",
            # ADDED: Include file_path from entity
            file_path=asset.file_path,
            title=getattr(asset, 'title', None),
            description=getattr(asset, 'description', None),
            prompt=truncated_prompt,
            model_used=asset.model_used,
            generation_time_ms=asset.generation_time_ms,
            # ADDED: Include generation_params
            generation_params=getattr(asset, 'generation_params', None),
            tags=getattr(asset, 'tags', []),
            is_favorite=getattr(asset, 'is_favorite', False),
            is_public=getattr(asset, 'is_public', False),
            view_count=getattr(asset, 'view_count', 0),
            download_count=getattr(asset, 'download_count', 0),
            conversation_id=str(asset.conversation_id) if asset.conversation_id else None,
            chart_configuration_id=str(asset.chart_configuration_id) if hasattr(asset, 'chart_configuration_id') and asset.chart_configuration_id else None,
            file_url=f"/api/assets/{asset.id}/file",
            thumbnail_url=f"/api/assets/{asset.id}/thumbnail" if asset.asset_type.value == "image" else None,
        )
    
    def to_dict(self, include_file_path: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Args:
            include_file_path: Whether to include the server-side file path (default False for security)
            
        Returns:
            Dictionary representation of the DTO
        """
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "asset_type": self.asset_type,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "formatted_file_size": self.formatted_file_size,
            "mime_type": self.mime_type,
            "created_at": self.created_at,
            "title": self.title,
            "description": self.description,
            "prompt": self.prompt,
            "model_used": self.model_used,
            "generation_time_ms": self.generation_time_ms,
            "tags": self.tags,
            "is_favorite": self.is_favorite,
            "is_public": self.is_public,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "conversation_id": self.conversation_id,
            "chart_configuration_id": self.chart_configuration_id,
            "file_url": self.file_url,
            "thumbnail_url": self.thumbnail_url,
        }
        
        # Only include file_path if explicitly requested (security measure)
        if include_file_path:
            result["file_path"] = self.file_path
            
        # Include generation_params if present
        if self.generation_params:
            result["generation_params"] = self.generation_params
            
        return result
    
    def to_response_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses (excludes sensitive data).
        """
        return self.to_dict(include_file_path=False)
    
    def to_admin_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for admin API responses (includes file_path).
        """
        return self.to_dict(include_file_path=True)


@dataclass
class AssetListDTO:
    """
    DTO for paginated asset list responses.
    """
    
    items: List[AssetDTO]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    def to_dict(self, include_file_path: bool = False) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "items": [item.to_dict(include_file_path=include_file_path) for item in self.items],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous,
        }
    
    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return self.to_dict(include_file_path=False)


@dataclass
class AssetStatsDTO:
    """
    DTO for asset statistics.
    """
    
    total_assets: int
    total_size_bytes: int
    formatted_total_size: str
    by_type: Dict[str, int]
    by_model: Dict[str, int]
    favorites_count: int
    total_views: int
    total_downloads: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_assets": self.total_assets,
            "total_size_bytes": self.total_size_bytes,
            "formatted_total_size": self.formatted_total_size,
            "by_type": self.by_type,
            "by_model": self.by_model,
            "favorites_count": self.favorites_count,
            "total_views": self.total_views,
            "total_downloads": self.total_downloads,
        }


@dataclass
class AssetUpdateDTO:
    """
    DTO for updating asset metadata.
    """
    
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    is_public: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.title is not None:
            result["title"] = self.title
        if self.description is not None:
            result["description"] = self.description
        if self.tags is not None:
            result["tags"] = self.tags
        if self.is_favorite is not None:
            result["is_favorite"] = self.is_favorite
        if self.is_public is not None:
            result["is_public"] = self.is_public
        return result