"""
Domain service for chart generation business logic.
Handles chart configuration validation, data processing, and generation orchestration.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import json

from src.domain.entities.chart_configuration import ChartConfiguration
from src.domain.entities.generated_asset import GeneratedAsset
from src.domain.value_objects.time_range import TimeRange
from src.domain.exceptions import (
    DomainValidationError,
    ChartGenerationFailedError,
    InvalidChartConfigurationError,
    DataSourceNotFoundError,
    InvalidDataFormatError,
    BusinessRuleViolationError,
)
from src.shared.constants import ChartType, AssetType
from src.shared.enums import ExportFormat


@dataclass
class ChartData:
    """
    Value object for processed chart data.
    """
    x_values: List[Any]
    y_values: Dict[str, List[float]]
    labels: Dict[str, str]
    metadata: Dict[str, Any]
    
    def validate(self) -> None:
        """Validate chart data."""
        if not self.x_values:
            raise InvalidChartConfigurationError("x_values", "X-axis values cannot be empty")
        
        if not self.y_values:
            raise InvalidChartConfigurationError("y_values", "At least one Y-axis series required")
        
        for series_name, values in self.y_values.items():
            if len(values) != len(self.x_values):
                raise InvalidChartConfigurationError(
                    series_name,
                    f"Length mismatch: expected {len(self.x_values)}, got {len(values)}"
                )
            
            if any(v is None or (isinstance(v, float) and (v != v)) for v in values):
                raise InvalidChartConfigurationError(
                    series_name,
                    "Series contains null or NaN values"
                )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Calculate basic statistics for the data."""
        stats = {}
        
        for series_name, values in self.y_values.items():
            clean_values = [v for v in values if v is not None]
            if clean_values:
                stats[series_name] = {
                    "min": min(clean_values),
                    "max": max(clean_values),
                    "mean": sum(clean_values) / len(clean_values),
                    "count": len(clean_values),
                    "total": sum(clean_values),
                }
        
        return stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x_values": self.x_values,
            "y_values": self.y_values,
            "labels": self.labels,
            "metadata": self.metadata,
            "statistics": self.get_statistics(),
        }


class ChartGenerationService:
    """
    Domain service for chart generation.
    Orchestrates the entire chart generation process.
    """
    
    # Supported data source types
    SUPPORTED_SOURCES = {"csv", "json", "api", "database", "in_memory"}
    
    # Chart type requirements
    CHART_REQUIREMENTS = {
        ChartType.LINE: {"min_series": 1, "max_series": 5, "min_points": 2},
        ChartType.BAR: {"min_series": 1, "max_series": 5, "min_points": 1, "max_points": 100},
        ChartType.SCATTER: {"min_series": 1, "max_series": 3, "min_points": 2},
        ChartType.AREA: {"min_series": 1, "max_series": 5, "min_points": 2},
        ChartType.HEATMAP: {"min_series": 2, "max_series": 2, "min_points": 4},
        ChartType.PIE: {"min_series": 1, "max_series": 1, "min_points": 1, "max_points": 20},
        ChartType.RADAR: {"min_series": 1, "max_series": 3, "min_points": 3},
        ChartType.CANDLESTICK: {"min_series": 1, "max_series": 1, "min_points": 2},
    }
    
    # Aggregation functions
    AGGREGATION_FUNCTIONS = {
        "sum": lambda x: sum(x),
        "avg": lambda x: sum(x) / len(x) if x else 0,
        "count": lambda x: len(x),
        "min": lambda x: min(x) if x else None,
        "max": lambda x: max(x) if x else None,
        "median": lambda x: sorted(x)[len(x)//2] if x else None,
        "std": lambda x: (sum((v - sum(x)/len(x))**2 for v in x) / len(x))**0.5 if x else 0,
    }
    
    def __init__(
        self,
        asset_repository,
        chart_config_repository,
        data_source_provider,
        chart_renderer,
    ):
        self.asset_repository = asset_repository
        self.chart_config_repository = chart_config_repository
        self.data_source_provider = data_source_provider
        self.chart_renderer = chart_renderer
    
    async def generate_chart(
        self,
        config: ChartConfiguration,
        user_id: UUID,
        export_format: ExportFormat = ExportFormat.PNG,
    ) -> Tuple[GeneratedAsset, ChartData]:
        """
        Generate a chart based on configuration.
        Returns the generated asset and the processed chart data.
        """
        # Validate configuration
        self._validate_configuration(config)
        
        # Load and process data
        raw_data = await self._load_data(config)
        chart_data = await self._process_data(config, raw_data)
        chart_data.validate()
        
        # Apply time range filter if specified
        if config.time_range:
            chart_data = self._apply_time_range_filter(chart_data, config.time_range)
        
        # Apply aggregation if group by is specified
        if config.group_by_column:
            chart_data = self._apply_aggregation(
                chart_data,
                config.group_by_column,
                config.aggregation_function,
            )
        
        # Apply limit if specified
        if config.limit and len(chart_data.x_values) > config.limit:
            chart_data = self._apply_limit(chart_data, config.limit)
        
        # Generate chart image/data
        rendered_chart = await self._render_chart(config, chart_data, export_format)
        
        # Create asset record
        asset = GeneratedAsset(
            user_id=user_id,
            asset_type=AssetType.CHART,
            file_path=rendered_chart["file_path"],
            file_name=rendered_chart["file_name"],
            file_size=rendered_chart["file_size"],
            mime_type=rendered_chart["mime_type"],
            title=config.title or config.name,
            description=config.description,
            chart_configuration_id=config.id,
            generation_params={
                "chart_type": config.chart_type.value,
                "data_source": config.data_source,
                "x_axis": config.x_axis_column,
                "y_axes": config.y_axis_columns,
                "aggregation": config.aggregation_function,
            },
            generation_time_ms=rendered_chart.get("generation_time_ms"),
        )
        
        # Save asset
        saved_asset = await self.asset_repository.add(asset)
        
        # Update config last used
        config.record_usage()
        await self.chart_config_repository.update(config)
        
        return saved_asset, chart_data
    
    async def generate_preview(
        self,
        config: ChartConfiguration,
    ) -> bytes:
        """
        Generate a quick preview of the chart.
        Returns image bytes.
        """
        self._validate_configuration(config)
        
        # Load sample/limited data for preview
        preview_config = self._create_preview_config(config)
        raw_data = await self._load_data(preview_config)
        chart_data = await self._process_data(preview_config, raw_data)
        
        # Render preview
        return await self.chart_renderer.render_preview(preview_config, chart_data)
    
    def _validate_configuration(self, config: ChartConfiguration) -> None:
        """
        Validate chart configuration against business rules.
        """
        # Check chart type requirements
        requirements = self.CHART_REQUIREMENTS.get(config.chart_type, {})
        
        if requirements:
            series_count = len(config.y_axis_columns)
            min_series = requirements.get("min_series", 1)
            max_series = requirements.get("max_series", 10)
            
            if series_count < min_series:
                raise InvalidChartConfigurationError(
                    "y_axis_columns",
                    f"Chart type '{config.chart_type.value}' requires at least {min_series} series"
                )
            
            if series_count > max_series:
                raise InvalidChartConfigurationError(
                    "y_axis_columns",
                    f"Chart type '{config.chart_type.value}' supports maximum {max_series} series"
                )
        
        # Validate data source
        source_type = config.data_source.split("://")[0] if "://" in config.data_source else "file"
        if source_type not in self.SUPPORTED_SOURCES and not config.data_source.endswith(tuple(self._get_supported_extensions())):
            raise DataSourceNotFoundError(config.data_source)
        
        # Validate aggregation for pie charts
        if config.chart_type == ChartType.PIE and config.aggregation_function not in ["sum", "avg", "count"]:
            raise InvalidChartConfigurationError(
                "aggregation_function",
                f"Pie chart only supports sum, avg, or count aggregation, got {config.aggregation_function}"
            )
    
    def _get_supported_extensions(self) -> List[str]:
        """Get supported file extensions."""
        return [".csv", ".json", ".xlsx", ".parquet"]
    
    def _create_preview_config(self, config: ChartConfiguration) -> ChartConfiguration:
        """
        Create a preview configuration with limited data.
        """
        preview_config = ChartConfiguration(
            user_id=config.user_id,
            name=f"{config.name} (Preview)",
            chart_type=config.chart_type,
            data_source=config.data_source,
            x_axis_column=config.x_axis_column,
            y_axis_columns=config.y_axis_columns[:2],  # Limit to 2 series
            group_by_column=config.group_by_column,
            aggregation_function=config.aggregation_function,
            title=config.title,
            x_axis_label=config.x_axis_label,
            y_axis_label=config.y_axis_label,
            color_scheme=config.color_scheme,
            theme=config.theme,
            width=400,  # Smaller for preview
            height=300,
            show_legend=config.show_legend,
            show_grid=config.show_grid,
            time_range=config.time_range,
            limit=100,  # Limit data points for preview
        )
        return preview_config
    
    async def _load_data(self, config: ChartConfiguration) -> List[Dict[str, Any]]:
        """
        Load data from the configured source.
        """
        try:
            return await self.data_source_provider.load_data(
                config.data_source,
                filters=config.filters,
            )
        except Exception as e:
            raise ChartGenerationFailedError(
                config.chart_type.value,
                f"Failed to load data: {str(e)}"
            )
    
    async def _process_data(
        self,
        config: ChartConfiguration,
        raw_data: List[Dict[str, Any]],
    ) -> ChartData:
        """
        Process raw data into chart-ready format.
        """
        if not raw_data:
            raise InvalidDataFormatError("non-empty dataset", "empty dataset")
        
        # Extract x-axis values
        x_values = []
        for row in raw_data:
            if config.x_axis_column in row:
                x_values.append(row[config.x_axis_column])
            else:
                raise InvalidDataFormatError(
                    f"column '{config.x_axis_column}'",
                    "column not found"
                )
        
        # Extract y-axis values for each series
        y_values = {}
        for y_column in config.y_axis_columns:
            series_values = []
            for row in raw_data:
                if y_column in row:
                    value = row[y_column]
                    # Convert to float if possible
                    try:
                        series_values.append(float(value) if value is not None else None)
                    except (ValueError, TypeError):
                        series_values.append(None)
                else:
                    series_values.append(None)
            
            y_values[y_column] = series_values
        
        # Create labels
        labels = {
            "x_axis": config.x_axis_label or config.x_axis_column,
            "y_axis": config.y_axis_label or ", ".join(config.y_axis_columns),
            "title": config.title or f"{config.chart_type.value.title()} Chart",
        }
        
        # Metadata
        metadata = {
            "chart_type": config.chart_type.value,
            "data_source": config.data_source,
            "total_rows": len(raw_data),
            "columns": list(raw_data[0].keys()) if raw_data else [],
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        return ChartData(
            x_values=x_values,
            y_values=y_values,
            labels=labels,
            metadata=metadata,
        )
    
    def _apply_time_range_filter(
        self,
        chart_data: ChartData,
        time_range: TimeRange,
    ) -> ChartData:
        """
        Filter chart data by time range.
        Assumes x_values are datetime-compatible.
        """
        filtered_indices = []
        
        for i, x_val in enumerate(chart_data.x_values):
            try:
                # Try to parse as datetime
                if isinstance(x_val, str):
                    date_val = datetime.fromisoformat(x_val.replace('Z', '+00:00'))
                elif isinstance(x_val, datetime):
                    date_val = x_val
                else:
                    # Can't parse, keep the point
                    filtered_indices.append(i)
                    continue
                
                if time_range.contains(date_val):
                    filtered_indices.append(i)
            except (ValueError, TypeError):
                # Not a date, keep the point
                filtered_indices.append(i)
        
        # Filter data
        new_x_values = [chart_data.x_values[i] for i in filtered_indices]
        new_y_values = {
            series: [values[i] for i in filtered_indices]
            for series, values in chart_data.y_values.items()
        }
        
        return ChartData(
            x_values=new_x_values,
            y_values=new_y_values,
            labels=chart_data.labels,
            metadata={
                **chart_data.metadata,
                "time_range_filtered": True,
                "time_range": time_range.to_dict(),
                "original_count": len(chart_data.x_values),
                "filtered_count": len(new_x_values),
            },
        )
    
    def _apply_aggregation(
        self,
        chart_data: ChartData,
        group_by_column: str,
        aggregation_function: str,
    ) -> ChartData:
        """
        Apply aggregation to chart data.
        """
        if aggregation_function not in self.AGGREGATION_FUNCTIONS:
            raise InvalidChartConfigurationError(
                "aggregation_function",
                f"Unsupported aggregation: {aggregation_function}"
            )
        
        agg_func = self.AGGREGATION_FUNCTIONS[aggregation_function]
        
        # Group by x_values (assuming x_values are the group keys)
        grouped_data: Dict[Any, Dict[str, List[float]]] = {}
        
        for i, group_key in enumerate(chart_data.x_values):
            if group_key not in grouped_data:
                grouped_data[group_key] = {series: [] for series in chart_data.y_values}
            
            for series, values in chart_data.y_values.items():
                if i < len(values) and values[i] is not None:
                    grouped_data[group_key][series].append(values[i])
        
        # Apply aggregation
        new_x_values = []
        new_y_values = {series: [] for series in chart_data.y_values}
        
        for group_key in sorted(grouped_data.keys()):
            new_x_values.append(group_key)
            for series in chart_data.y_values:
                values = grouped_data[group_key][series]
                aggregated = agg_func(values) if values else None
                new_y_values[series].append(aggregated)
        
        return ChartData(
            x_values=new_x_values,
            y_values=new_y_values,
            labels=chart_data.labels,
            metadata={
                **chart_data.metadata,
                "aggregated": True,
                "aggregation_function": aggregation_function,
                "group_by": group_by_column,
                "original_count": len(chart_data.x_values),
                "aggregated_count": len(new_x_values),
            },
        )
    
    def _apply_limit(self, chart_data: ChartData, limit: int) -> ChartData:
        """
        Apply limit to chart data (take most recent/last N points).
        """
        if limit >= len(chart_data.x_values):
            return chart_data
        
        return ChartData(
            x_values=chart_data.x_values[-limit:],
            y_values={
                series: values[-limit:]
                for series, values in chart_data.y_values.items()
            },
            labels=chart_data.labels,
            metadata={
                **chart_data.metadata,
                "limited": True,
                "limit": limit,
                "original_count": len(chart_data.x_values),
            },
        )
    
    async def _render_chart(
        self,
        config: ChartConfiguration,
        chart_data: ChartData,
        export_format: ExportFormat,
    ) -> Dict[str, Any]:
        """
        Render the chart using the chart renderer.
        """
        try:
            return await self.chart_renderer.render(
                config=config,
                data=chart_data,
                export_format=export_format,
            )
        except Exception as e:
            raise ChartGenerationFailedError(
                config.chart_type.value,
                f"Failed to render chart: {str(e)}"
            )
    
    def get_supported_chart_types(self) -> List[Dict[str, Any]]:
        """
        Get information about supported chart types.
        """
        return [
            {
                "type": chart_type.value,
                "description": self._get_chart_description(chart_type),
                "requirements": self.CHART_REQUIREMENTS.get(chart_type, {}),
                "best_for": self._get_chart_best_for(chart_type),
            }
            for chart_type in ChartType
        ]
    
    def _get_chart_description(self, chart_type: ChartType) -> str:
        """Get description for chart type."""
        descriptions = {
            ChartType.LINE: "Best for showing trends over time or continuous data",
            ChartType.BAR: "Best for comparing categories or discrete values",
            ChartType.SCATTER: "Best for showing relationships between two variables",
            ChartType.AREA: "Best for showing cumulative totals over time",
            ChartType.HEATMAP: "Best for showing patterns in large datasets",
            ChartType.PIE: "Best for showing proportions of a whole (use sparingly)",
            ChartType.RADAR: "Best for comparing multiple variables across categories",
            ChartType.CANDLESTICK: "Best for financial data showing open/high/low/close",
        }
        return descriptions.get(chart_type, "General purpose chart")
    
    def _get_chart_best_for(self, chart_type: ChartType) -> List[str]:
        """Get best use cases for chart type."""
        use_cases = {
            ChartType.LINE: ["Time series", "Trends", "Continuous data"],
            ChartType.BAR: ["Comparisons", "Rankings", "Categorical data"],
            ChartType.SCATTER: ["Correlation", "Distribution", "Outliers"],
            ChartType.AREA: ["Volume", "Cumulative values", "Stacked trends"],
            ChartType.HEATMAP: ["Correlation matrix", "Density", "Patterns"],
            ChartType.PIE: ["Proportions", "Market share", "Budget breakdown"],
            ChartType.RADAR: ["Performance metrics", "Skill assessment", "Multi-variable comparison"],
            ChartType.CANDLESTICK: ["Stock prices", "Forex", "Cryptocurrency"],
        }
        return use_cases.get(chart_type, ["General data visualization"])
    
    def suggest_chart_type(self, chart_data: ChartData) -> ChartType:
        """
        Suggest the best chart type based on data characteristics.
        """
        num_points = len(chart_data.x_values)
        num_series = len(chart_data.y_values)
        
        # Check if x-axis looks like time series
        is_time_series = self._is_time_series(chart_data.x_values)
        
        # Check if data is categorical
        is_categorical = self._is_categorical(chart_data.x_values)
        
        # Check for percentage/proportion data
        is_percentage = self._is_percentage_data(chart_data)
        
        if is_time_series and num_series <= 3:
            return ChartType.LINE
        elif is_categorical and num_points <= 20:
            if num_series == 1 and is_percentage:
                return ChartType.PIE
            return ChartType.BAR
        elif num_series == 2 and num_points > 10:
            return ChartType.SCATTER
        elif num_series == 1 and num_points > 50:
            return ChartType.AREA
        elif num_series == 4 and all(v == "OHLC" for v in chart_data.y_values.keys()):
            return ChartType.CANDLESTICK
        else:
            return ChartType.BAR
    
    def _is_time_series(self, x_values: List[Any]) -> bool:
        """Check if x-values represent time series."""
        if not x_values:
            return False
        
        # Check if values are dates
        date_count = 0
        for val in x_values[:10]:  # Sample first 10
            try:
                if isinstance(val, str):
                    datetime.fromisoformat(val.replace('Z', '+00:00'))
                    date_count += 1
                elif isinstance(val, datetime):
                    date_count += 1
            except (ValueError, TypeError):
                pass
        
        return date_count >= len(x_values[:10]) * 0.7  # 70% threshold
    
    def _is_categorical(self, x_values: List[Any]) -> bool:
        """Check if x-values are categorical."""
        if not x_values:
            return False
        
        unique_values = set(str(v) for v in x_values)
        unique_ratio = len(unique_values) / len(x_values)
        
        # If less than 20% unique values, likely categorical
        return unique_ratio < 0.2 or all(isinstance(v, str) for v in x_values)
    
    def _is_percentage_data(self, chart_data: ChartData) -> bool:
        """Check if data represents percentages."""
        for series_values in chart_data.y_values.values():
            clean_values = [v for v in series_values if v is not None]
            if clean_values:
                total = sum(clean_values)
                # Check if values sum to approximately 100
                if 99 <= total <= 101:
                    return True
                # Check if all values are between 0 and 100
                if all(0 <= v <= 100 for v in clean_values):
                    return True
        return False
    
    async def export_chart_data(
        self,
        chart_data: ChartData,
        export_format: ExportFormat,
    ) -> Tuple[str, bytes]:
        """
        Export chart data in various formats.
        Returns (filename, data_bytes).
        """
        import io
        import csv
        import json as json_module
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if export_format == ExportFormat.CSV:
            filename = f"chart_data_{timestamp}.csv"
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            headers = ["x"] + list(chart_data.y_values.keys())
            writer.writerow(headers)
            
            # Write data
            for i, x_val in enumerate(chart_data.x_values):
                row = [x_val]
                for series_values in chart_data.y_values.values():
                    row.append(series_values[i] if i < len(series_values) else "")
                writer.writerow(row)
            
            return filename, output.getvalue().encode("utf-8")
        
        elif export_format == ExportFormat.JSON:
            filename = f"chart_data_{timestamp}.json"
            data = chart_data.to_dict()
            return filename, json_module.dumps(data, indent=2, default=str).encode("utf-8")
        
        else:
            raise InvalidChartConfigurationError(
                "export_format",
                f"Unsupported export format: {export_format.value}"
            )