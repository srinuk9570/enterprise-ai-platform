"""
Generated asset entity for AI-generated images and charts.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List  # ADD List HERE
from uuid import UUID, uuid4

from src.shared.constants import AssetType
from src.domain.exceptions import DomainValidationError


@dataclass
class GeneratedAsset:
    """
    Generated asset entity.
    Represents AI-generated content like images or exported charts.
    """
    
    user_id: UUID
    asset_type: AssetType
    file_path: str
    file_name: str
    file_size: int
    mime_type: str
    
    # Generation metadata
    prompt: Optional[str] = None
    model_used: Optional[str] = None
    generation_params: Dict[str, Any] = field(default_factory=dict)
    generation_time_ms: Optional[float] = None
    
    # Database fields
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Additional metadata
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_favorite: bool = False
    is_public: bool = False
    view_count: int = 0
    download_count: int = 0
    
    # Optional relationships
    conversation_id: Optional[UUID] = None
    chart_configuration_id: Optional[UUID] = None
    
    def __post_init__(self) -> None:
        """Validate asset after initialization."""
        self._validate_file_name()
        self._validate_file_size()
        self._validate_mime_type()
        self._validate_prompt()
    
    def _validate_file_name(self) -> None:
        """Validate file name."""
        if not self.file_name:
            raise DomainValidationError("File name cannot be empty")
        if len(self.file_name) > 255:
            raise DomainValidationError("File name must be at most 255 characters")
        
        # Check for invalid characters
        invalid_chars = set('<>:"/\\|?*')
        if any(c in invalid_chars for c in self.file_name):
            raise DomainValidationError("File name contains invalid characters")
    
    def _validate_file_size(self) -> None:
        """Validate file size."""
        if self.file_size < 0:
            raise DomainValidationError("File size cannot be negative")
        
        max_sizes = {
            AssetType.IMAGE: 50 * 1024 * 1024,  # 50 MB
            AssetType.CHART: 10 * 1024 * 1024,  # 10 MB
            AssetType.EXPORT: 100 * 1024 * 1024,  # 100 MB
        }
        
        max_size = max_sizes.get(self.asset_type, 10 * 1024 * 1024)
        if self.file_size > max_size:
            raise DomainValidationError(
                f"File size exceeds maximum of {max_size / (1024*1024):.0f} MB for {self.asset_type.value}"
            )
    
    def _validate_mime_type(self) -> None:
        """Validate MIME type."""
        valid_mime_types = {
            AssetType.IMAGE: ["image/png", "image/jpeg", "image/gif", "image/webp", "image/svg+xml"],
            AssetType.CHART: ["image/png", "image/svg+xml", "application/pdf"],
            AssetType.EXPORT: ["text/csv", "application/json", "application/pdf", "text/markdown"],
        }
        
        allowed = valid_mime_types.get(self.asset_type, [])
        if allowed and self.mime_type not in allowed:
            raise DomainValidationError(
                f"Invalid MIME type '{self.mime_type}' for {self.asset_type.value}"
            )
    
    def _validate_prompt(self) -> None:
        """Validate prompt if present."""
        if self.prompt and len(self.prompt) > 4000:
            raise DomainValidationError("Prompt must be at most 4000 characters")
    
    def update_title(self, title: str) -> None:
        """Update asset title."""
        if len(title) > 200:
            raise DomainValidationError("Title must be at most 200 characters")
        self.title = title
    
    def update_description(self, description: str) -> None:
        """Update asset description."""
        if len(description) > 1000:
            raise DomainValidationError("Description must be at most 1000 characters")
        self.description = description
    
    def increment_view_count(self) -> None:
        """Increment view count."""
        self.view_count += 1
    
    def increment_download_count(self) -> None:
        """Increment download count."""
        self.download_count += 1
    
    def toggle_favorite(self) -> None:
        """Toggle favorite status."""
        self.is_favorite = not self.is_favorite
    
    def toggle_public(self) -> None:
        """Toggle public/private status."""
        self.is_public = not self.is_public
    
    def add_tag(self, tag: str) -> None:
        """Add a tag."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def add_generation_param(self, key: str, value: Any) -> None:
        """Add generation parameter."""
        self.generation_params[key] = value
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return self.file_name.split(".")[-1] if "." in self.file_name else ""
    
    @property
    def formatted_file_size(self) -> str:
        """Get human-readable file size."""
        size = self.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    @property
    def is_image(self) -> bool:
        """Check if asset is an image."""
        return self.asset_type == AssetType.IMAGE
    
    @property
    def is_chart(self) -> bool:
        """Check if asset is a chart."""
        return self.asset_type == AssetType.CHART
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "asset_type": self.asset_type.value,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "formatted_file_size": self.formatted_file_size,
            "mime_type": self.mime_type,
            "prompt": self.prompt,
            "model_used": self.model_used,
            "generation_params": self.generation_params,
            "generation_time_ms": self.generation_time_ms,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "is_favorite": self.is_favorite,
            "is_public": self.is_public,
            "view_count": self.view_count,
            "download_count": self.download_count,
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "chart_configuration_id": str(self.chart_configuration_id) if self.chart_configuration_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "file_extension": self.file_extension,
        }