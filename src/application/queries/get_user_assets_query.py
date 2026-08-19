"""
Query for retrieving user assets.
"""
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID


@dataclass
class GetUserAssetsQuery:
    """
    Query to get user's generated assets.
    """
    
    user_id: UUID
    asset_type: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    conversation_id: Optional[UUID] = None
    skip: int = 0
    limit: int = 50
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if self.limit < 1 or self.limit > 100:
            errors.append("Limit must be between 1 and 100")
        
        return len(errors) == 0, errors