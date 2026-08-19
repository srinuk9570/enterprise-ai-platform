"""
Base query class for CQRS pattern.
"""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


@dataclass
class BaseQuery:
    """
    Base class for all queries.
    Queries represent a request for data without side effects.
    """
    
    # Query metadata
    query_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    requested_by: Optional[UUID] = None
    correlation_id: Optional[str] = None
    
    # Pagination
    skip: int = 0
    limit: int = 100
    
    # Sorting
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    
    def validate_pagination(self) -> tuple[bool, list[str]]:
        """Validate pagination parameters."""
        errors = []
        
        if self.skip < 0:
            errors.append("Skip cannot be negative")
        
        if self.limit < 1 or self.limit > 1000:
            errors.append("Limit must be between 1 and 1000")
        
        if self.sort_order not in ["asc", "desc"]:
            errors.append("Sort order must be 'asc' or 'desc'")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> dict:
        """Convert query to dictionary for logging."""
        return {
            "query_type": self.__class__.__name__,
            "query_id": str(self.query_id),
            "timestamp": self.timestamp.isoformat(),
            "requested_by": str(self.requested_by) if self.requested_by else None,
            "correlation_id": self.correlation_id,
        }