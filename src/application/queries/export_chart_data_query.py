"""
Query for exporting chart data.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass
class ExportChartDataQuery:
    """
    Query to export chart data in various formats.
    """
    
    chart_config_id: UUID
    user_id: UUID
    export_format: str = "png"
    include_raw_data: bool = False
    include_statistics: bool = True
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    limit: Optional[int] = None
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate query parameters."""
        errors = []
        
        if not self.chart_config_id:
            errors.append("Chart configuration ID is required")
        
        if not self.user_id:
            errors.append("User ID is required")
        
        valid_formats = ["png", "svg", "pdf", "csv", "json"]
        if self.export_format not in valid_formats:
            errors.append(f"Export format must be one of: {', '.join(valid_formats)}")
        
        return len(errors) == 0, errors