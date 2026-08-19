"""
Query for searching conversations.
"""
from dataclasses import dataclass
from typing import Optional, List
from uuid import UUID


@dataclass
class SearchConversationsQuery:
    """
    Query to search conversations by title or content.
    """
    
    user_id: UUID
    query: str
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    model_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    search_in_messages: bool = True
    case_sensitive: bool = False
    skip: int = 0
    limit: int = 20
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.query or len(self.query.strip()) < 2:
            errors.append("Search query must be at least 2 characters")
        
        return len(errors) == 0, errors