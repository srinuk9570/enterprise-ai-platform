"""
Query for retrieving user dashboard data.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class GetUserDashboardQuery:
    """
    Query to get user dashboard statistics and overview.
    """
    
    user_id: UUID
    period: str = "30d"
    include_conversations: bool = True
    include_assets: bool = True
    include_usage_stats: bool = True
    include_recent_activity: bool = True
    recent_conversations_limit: int = 10
    recent_assets_limit: int = 10
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate query parameters."""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        valid_periods = ["1d", "7d", "30d", "90d", "all"]
        if self.period not in valid_periods:
            errors.append(f"Period must be one of: {', '.join(valid_periods)}")
        
        return len(errors) == 0, errors