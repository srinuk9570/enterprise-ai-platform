"""
Chart configuration entity for AI-generated charts.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any  # ADD List HERE
from uuid import UUID, uuid4

from src.shared.constants import ChartType
from src.domain.exceptions import DomainValidationError
from src.domain.value_objects.time_range import TimeRange



@dataclass
class ChartConfiguration:
    """
    Chart configuration entity.
    Defines how a chart should be rendered.
    """
    
    user_id: UUID
    name: str
    chart_type: ChartType
    data_source: str  # Can be CSV path, SQL query, or API endpoint
    
    # Data configuration
    x_axis_column: str
    y_axis_columns: List[str] = field(default_factory=list)
    group_by_column: Optional[str] = None
    aggregation_function: str = "sum"  # sum, avg, count, min, max
    
    # Visual configuration
    title: Optional[str] = None
    x_axis_label: Optional[str] = None
    y_axis_label: Optional[str] = None
    color_scheme: str = "default"
    theme: str = "dark"
    width: int = 800
    height: int = 400
    
    # Advanced options
    show_legend: bool = True
    show_grid: bool = True
    show_tooltips: bool = True
    stacked: bool = False
    normalized: bool = False
    cumulative: bool = False
    
    # Filters
    time_range: Optional[TimeRange] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: Optional[int] = 1000
    
    # Database fields
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = None
    
    # Additional options
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    is_public: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate_name()
        self._validate_columns()
        self._validate_dimensions()
        self._validate_aggregation()
    
    def _validate_name(self) -> None:
        """Validate chart name."""
        if not self.name or len(self.name.strip()) == 0:
            raise DomainValidationError("Chart name cannot be empty")
        if len(self.name) > 100:
            raise DomainValidationError("Chart name must be at most 100 characters")
        self.name = self.name.strip()
    
    def _validate_columns(self) -> None:
        """Validate column configurations."""
        if not self.x_axis_column:
            raise DomainValidationError("X-axis column must be specified")
        
        if not self.y_axis_columns:
            raise DomainValidationError("At least one Y-axis column must be specified")
        
        if len(self.y_axis_columns) > 5:
            raise DomainValidationError("Maximum 5 Y-axis columns allowed")
    
    def _validate_dimensions(self) -> None:
        """Validate chart dimensions."""
        if self.width < 200 or self.width > 2000:
            raise DomainValidationError("Width must be between 200 and 2000 pixels")
        
        if self.height < 200 or self.height > 2000:
            raise DomainValidationError("Height must be between 200 and 2000 pixels")
    
    def _validate_aggregation(self) -> None:
        """Validate aggregation function."""
        valid_aggregations = ["sum", "avg", "count", "min", "max", "median", "std"]
        if self.aggregation_function not in valid_aggregations:
            raise DomainValidationError(
                f"Invalid aggregation function. Must be one of: {', '.join(valid_aggregations)}"
            )
    
    def update_name(self, new_name: str) -> None:
        """Update chart name."""
        self.name = new_name
        self._validate_name()
        self.updated_at = datetime.utcnow()
    
    def update_dimensions(self, width: int, height: int) -> None:
        """Update chart dimensions."""
        self.width = width
        self.height = height
        self._validate_dimensions()
        self.updated_at = datetime.utcnow()
    
    def update_columns(
        self,
        x_axis_column: Optional[str] = None,
        y_axis_columns: Optional[List[str]] = None,
        group_by_column: Optional[str] = None,
    ) -> None:
        """Update column configuration."""
        if x_axis_column:
            self.x_axis_column = x_axis_column
        
        if y_axis_columns:
            self.y_axis_columns = y_axis_columns
        
        if group_by_column is not None:
            self.group_by_column = group_by_column
        
        self._validate_columns()
        self.updated_at = datetime.utcnow()
    
    def add_filter(self, column: str, value: Any) -> None:
        """Add a filter condition."""
        self.filters[column] = value
        self.updated_at = datetime.utcnow()
    
    def remove_filter(self, column: str) -> None:
        """Remove a filter condition."""
        if column in self.filters:
            del self.filters[column]
            self.updated_at = datetime.utcnow()
    
    def clear_filters(self) -> None:
        """Clear all filters."""
        self.filters.clear()
        self.updated_at = datetime.utcnow()
    
    def record_usage(self) -> None:
        """Record that chart was used."""
        self.last_used_at = datetime.utcnow()
    
    def toggle_public(self) -> None:
        """Toggle public/private status."""
        self.is_public = not self.is_public
        self.updated_at = datetime.utcnow()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "chart_type": self.chart_type.value,
            "data_source": self.data_source,
            "x_axis_column": self.x_axis_column,
            "y_axis_columns": self.y_axis_columns,
            "group_by_column": self.group_by_column,
            "aggregation_function": self.aggregation_function,
            "title": self.title,
            "x_axis_label": self.x_axis_label,
            "y_axis_label": self.y_axis_label,
            "color_scheme": self.color_scheme,
            "theme": self.theme,
            "width": self.width,
            "height": self.height,
            "show_legend": self.show_legend,
            "show_grid": self.show_grid,
            "show_tooltips": self.show_tooltips,
            "stacked": self.stacked,
            "normalized": self.normalized,
            "cumulative": self.cumulative,
            "time_range": self.time_range.to_dict() if self.time_range else None,
            "filters": self.filters,
            "limit": self.limit,
            "description": self.description,
            "tags": self.tags,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
        }