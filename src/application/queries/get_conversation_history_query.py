"""
Query for retrieving conversation history.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from src.application.queries.base_query import BaseQuery


@dataclass
class GetConversationHistoryQuery:
    """
    Query to get conversation history with messages.
    """
    
    conversation_id: UUID
    user_id: UUID
    
    # Filtering options
    include_messages: bool = True
    message_limit: Optional[int] = 100
    include_archived: bool = False
    include_system_messages: bool = False
    
    # Message filtering
    search_term: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # Pagination
    skip: int = 0
    limit: int = 100
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate query parameters."""
        errors = []
        
        if not self.conversation_id:
            errors.append("Conversation ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if self.message_limit and (self.message_limit < 1 or self.message_limit > 1000):
            errors.append("Message limit must be between 1 and 1000")
        
        if self.skip < 0:
            errors.append("Skip cannot be negative")
        
        if self.limit < 1 or self.limit > 1000:
            errors.append("Limit must be between 1 and 1000")
        
        return len(errors) == 0, errors