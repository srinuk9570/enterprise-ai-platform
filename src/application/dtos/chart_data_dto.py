"""
Chart Data Transfer Object.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ChartDataDTO:
    """
    DTO for chart data sent to clients.
    """
    
    x_values: List[Any]
    y_values: Dict[str, List[float]]
    labels: Dict[str, str]
    metadata: Dict[str, Any]
    statistics: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_chart_data(cls, chart_data) -> "ChartDataDTO":
        """
        Create DTO from chart data value object.
        """
        return cls(
            x_values=chart_data.x_values,
            y_values=chart_data.y_values,
            labels=chart_data.labels,
            metadata=chart_data.metadata,
            statistics=chart_data.get_statistics(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x_values": self.x_values,
            "y_values": self.y_values,
            "labels": self.labels,
            "metadata": self.metadata,
            "statistics": self.statistics,
        }
    
    def to_csv_format(self) -> str:
        """Convert to CSV string."""
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        headers = ["x"] + list(self.y_values.keys())
        writer.writerow(headers)
        
        # Data rows
        for i, x_val in enumerate(self.x_values):
            row = [x_val]
            for series_values in self.y_values.values():
                row.append(series_values[i] if i < len(series_values) else "")
            writer.writerow(row)
        
        return output.getvalue()