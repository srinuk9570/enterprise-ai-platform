"""
Command for creating a chart.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.application.commands.base_command import BaseCommand
from src.shared.constants import ChartType


@dataclass
class CreateChartCommand(BaseCommand):
    """
    Command to create/generate a chart.
    """
    
    user_id: UUID
    name: str
    chart_type: ChartType
    data_source: str
    x_axis_column: str
    y_axis_columns: List[str]
    
    # Optional configuration
    group_by_column: Optional[str] = None
    aggregation_function: str = "sum"
    title: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_scheme: str = "default"
    theme: str = "dark"
    width: int = 800
    height: int = 400
    
    # Display options
    show_legend: bool = True
    show_grid: bool = True
    show_tooltips: bool = True
    stacked: bool = False
    
    # Data filters
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = 1000
    
    # Export options
    export_format: str = "png"
    
    # Context
    conversation_id: Optional[UUID] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate command data."""
        errors = []
        
        if not self.user_id:
            errors.append("User ID is required")
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Chart name is required")
        
        if len(self.name) > 100:
            errors.append("Chart name must be at most 100 characters")
        
        if not self.data_source:
            errors.append("Data source is required")
        
        if not self.x_axis_column:
            errors.append("X-axis column is required")
        
        if not self.y_axis_columns:
            errors.append("At least one Y-axis column is required")
        
        if len(self.y_axis_columns) > 5:
            errors.append("Maximum 5 Y-axis columns allowed")
        
        valid_aggregations = ["sum", "avg", "count", "min", "max", "median", "std"]
        if self.aggregation_function not in valid_aggregations:
            errors.append(f"Invalid aggregation function: {self.aggregation_function}")
        
        if self.width < 200 or self.width > 2000:
            errors.append("Width must be between 200 and 2000")
        
        if self.height < 200 or self.height > 2000:
            errors.append("Height must be between 200 and 2000")
        
        valid_formats = ["png", "svg", "pdf", "csv", "json"]
        if self.export_format not in valid_formats:
            errors.append(f"Invalid export format: {self.export_format}")
        
        return len(errors) == 0, errors