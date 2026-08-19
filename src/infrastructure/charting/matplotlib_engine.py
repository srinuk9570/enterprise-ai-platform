"""
Matplotlib engine wrapper for chart generation.
"""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
import io
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from pathlib import Path

from src.shared.config import settings
from src.infrastructure.charting.themes import DarkTheme, LightTheme, ChartTheme
from src.infrastructure.charting.exporters import PNGExporter, SVGExporter

logger = logging.getLogger(__name__)


class MatplotlibEngine:
    """
    Matplotlib wrapper for chart generation with theme support.
    """
    
    def __init__(self, theme: Optional[ChartTheme] = None):
        self.theme = theme or DarkTheme()
        self.png_exporter = PNGExporter()
        self.svg_exporter = SVGExporter()
        self._setup_matplotlib()
    
    def _setup_matplotlib(self) -> None:
        """Setup matplotlib global settings."""
        plt.rcParams['figure.dpi'] = 100
        plt.rcParams['savefig.dpi'] = 150
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['Inter', 'DejaVu Sans', 'Arial']
        plt.rcParams['axes.unicode_minus'] = False
    
    def set_theme(self, theme: ChartTheme) -> None:
        """Change the chart theme."""
        self.theme = theme
        logger.debug(f"Chart theme changed to {theme.name}")
    
    def create_figure(
        self,
        figsize: Tuple[int, int] = (10, 6),
        dpi: int = 100,
    ) -> Tuple[Figure, Axes]:
        """
        Create a new figure and axes with theme applied.
        
        Args:
            figsize: Figure size in inches
            dpi: DPI for the figure
        
        Returns:
            Tuple of (figure, axes)
        """
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        
        # Apply theme
        self.theme.apply(ax, fig)
        
        return fig, ax
    
    def render_line_chart(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray, Dict[str, Union[List, np.ndarray]]],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        show_legend: bool = True,
        show_grid: bool = True,
        line_width: float = 2.0,
        markers: bool = False,
        **kwargs,
    ) -> Figure:
        """
        Render a line chart.
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data (single series or dict of series)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_legend: Whether to show legend
            show_grid: Whether to show grid
            line_width: Width of lines
            markers: Whether to show markers
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.create_figure(**kwargs)
        
        if isinstance(y_data, dict):
            for label, data in y_data.items():
                ax.plot(
                    x_data, data,
                    label=label,
                    linewidth=line_width,
                    marker='o' if markers else None,
                    markersize=4 if markers else None,
                )
        else:
            ax.plot(
                x_data, y_data,
                linewidth=line_width,
                marker='o' if markers else None,
                markersize=4 if markers else None,
            )
        
        self._apply_labels(ax, title, xlabel, ylabel)
        
        if show_legend and isinstance(y_data, dict):
            ax.legend(loc='best', frameon=True)
        
        ax.grid(show_grid, alpha=0.3)
        
        return fig
    
    def render_bar_chart(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray, Dict[str, Union[List, np.ndarray]]],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        show_legend: bool = True,
        show_grid: bool = True,
        stacked: bool = False,
        horizontal: bool = False,
        bar_width: float = 0.8,
        **kwargs,
    ) -> Figure:
        """
        Render a bar chart.
        
        Args:
            x_data: X-axis data (categories)
            y_data: Y-axis data
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_legend: Whether to show legend
            show_grid: Whether to show grid
            stacked: Whether to stack bars
            horizontal: Whether to use horizontal bars
            bar_width: Width of bars
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.create_figure(**kwargs)
        
        x_pos = np.arange(len(x_data))
        
        if isinstance(y_data, dict):
            if stacked:
                bottom = np.zeros(len(x_data))
                for label, data in y_data.items():
                    bar_func = ax.barh if horizontal else ax.bar
                    bar_func(
                        x_pos, data,
                        width=bar_width if horizontal else None,
                        height=bar_width if not horizontal else None,
                        bottom=bottom if not horizontal else None,
                        left=bottom if horizontal else None,
                        label=label,
                    )
                    bottom += np.array(data)
            else:
                n_series = len(y_data)
                bar_width_adjusted = bar_width / n_series
                
                for i, (label, data) in enumerate(y_data.items()):
                    offset = (i - n_series / 2 + 0.5) * bar_width_adjusted
                    bar_func = ax.barh if horizontal else ax.bar
                    bar_func(
                        x_pos + offset,
                        data,
                        width=bar_width_adjusted if horizontal else None,
                        height=bar_width_adjusted if not horizontal else None,
                        label=label,
                    )
        else:
            bar_func = ax.barh if horizontal else ax.bar
            bar_func(
                x_pos,
                y_data,
                width=bar_width if horizontal else None,
                height=bar_width if not horizontal else None,
            )
        
        if horizontal:
            ax.set_yticks(x_pos)
            ax.set_yticklabels(x_data)
            ax.set_xlabel(ylabel)
            ax.set_ylabel(xlabel)
        else:
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_data, rotation=45, ha='right')
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        
        ax.set_title(title)
        
        if show_legend and isinstance(y_data, dict):
            ax.legend(loc='best', frameon=True)
        
        ax.grid(show_grid, axis='y', alpha=0.3)
        
        fig.tight_layout()
        
        return fig
    
    def render_scatter_plot(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        show_grid: bool = True,
        color: Optional[Union[str, List]] = None,
        size: Optional[Union[float, List]] = None,
        alpha: float = 0.7,
        trendline: bool = False,
        **kwargs,
    ) -> Figure:
        """
        Render a scatter plot.
        
        Args:
            x_data: X-axis data
            y_data: Y-axis data
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_grid: Whether to show grid
            color: Point color(s)
            size: Point size(s)
            alpha: Point transparency
            trendline: Whether to add trendline
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.create_figure(**kwargs)
        
        scatter = ax.scatter(
            x_data, y_data,
            c=color if color else self.theme.primary_color,
            s=size if size else 50,
            alpha=alpha,
            edgecolors='white',
            linewidth=0.5,
        )
        
        if trendline and len(x_data) > 1:
            z = np.polyfit(x_data, y_data, 1)
            p = np.poly1d(z)
            ax.plot(
                x_data, p(x_data),
                color=self.theme.accent_color,
                linestyle='--',
                linewidth=2,
                label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}',
            )
            ax.legend(loc='best')
        
        self._apply_labels(ax, title, xlabel, ylabel)
        ax.grid(show_grid, alpha=0.3)
        
        return fig
    
    def render_heatmap(
        self,
        data: Union[List[List], np.ndarray],
        x_labels: Optional[List] = None,
        y_labels: Optional[List] = None,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        cmap: str = "viridis",
        annotate: bool = True,
        annotate_fmt: str = ".2f",
        **kwargs,
    ) -> Figure:
        """
        Render a heatmap.
        
        Args:
            data: 2D array of values
            x_labels: X-axis labels
            y_labels: Y-axis labels
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            cmap: Colormap name
            annotate: Whether to show values
            annotate_fmt: Format for annotations
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.create_figure(**kwargs)
        
        data_array = np.array(data)
        
        im = ax.imshow(data_array, cmap=cmap, aspect='auto')
        
        if x_labels:
            ax.set_xticks(np.arange(len(x_labels)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
        
        if y_labels:
            ax.set_yticks(np.arange(len(y_labels)))
            ax.set_yticklabels(y_labels)
        
        if annotate:
            for i in range(data_array.shape[0]):
                for j in range(data_array.shape[1]):
                    text = ax.text(
                        j, i,
                        format(data_array[i, j], annotate_fmt),
                        ha="center", va="center",
                        color="white" if data_array[i, j] < data_array.mean() else "black",
                        fontsize=10,
                    )
        
        plt.colorbar(im, ax=ax)
        
        self._apply_labels(ax, title, xlabel, ylabel)
        
        fig.tight_layout()
        
        return fig
    
    def render_pie_chart(
        self,
        values: Union[List, np.ndarray],
        labels: Optional[List] = None,
        title: str = "",
        show_percentages: bool = True,
        explode: Optional[List] = None,
        startangle: int = 90,
        **kwargs,
    ) -> Figure:
        """
        Render a pie chart.
        
        Args:
            values: Slice values
            labels: Slice labels
            title: Chart title
            show_percentages: Whether to show percentages
            explode: Explode offsets for slices
            startangle: Starting angle
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.create_figure(**kwargs)
        
        if show_percentages:
            autopct = '%1.1f%%'
        else:
            autopct = None
        
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct=autopct,
            explode=explode,
            startangle=startangle,
            colors=self.theme.color_palette,
            textprops={'color': self.theme.text_color},
        )
        
        ax.set_title(title)
        
        return fig
    
    def _apply_labels(
        self,
        ax: Axes,
        title: str,
        xlabel: str,
        ylabel: str,
    ) -> None:
        """Apply labels to axes."""
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)
    
    def save_figure(
        self,
        fig: Figure,
        filepath: Union[str, Path],
        format: str = "png",
        dpi: int = 150,
        bbox_inches: str = "tight",
    ) -> Path:
        """
        Save figure to file.
        
        Args:
            fig: Figure to save
            filepath: Output path
            format: Output format
            dpi: Resolution
            bbox_inches: Bounding box
        
        Returns:
            Path to saved file
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        fig.savefig(
            filepath,
            format=format,
            dpi=dpi,
            bbox_inches=bbox_inches,
            facecolor=fig.get_facecolor(),
            edgecolor='none',
        )
        
        logger.info(f"Chart saved to {filepath}")
        
        return filepath
    
    def figure_to_bytes(
        self,
        fig: Figure,
        format: str = "png",
        dpi: int = 150,
    ) -> bytes:
        """
        Convert figure to bytes.
        
        Args:
            fig: Figure to convert
            format: Output format
            dpi: Resolution
        
        Returns:
            Image bytes
        """
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format=format,
            dpi=dpi,
            bbox_inches='tight',
            facecolor=fig.get_facecolor(),
        )
        buf.seek(0)
        return buf.getvalue()
    
    def close_figure(self, fig: Figure) -> None:
        """Close and cleanup figure."""
        plt.close(fig)
    
    async def render(
        self,
        config: Any,
        data: Any,
        export_format: str = "png",
    ) -> Dict[str, Any]:
        """
        Render chart based on configuration.
        
        Args:
            config: Chart configuration
            data: Processed chart data
            export_format: Output format
        
        Returns:
            Dictionary with file info
        """
        from datetime import datetime
        import hashlib
        
        # Create chart based on type
        chart_type = config.chart_type.value if hasattr(config.chart_type, 'value') else str(config.chart_type)
        
        if chart_type == "line":
            fig = self.render_line_chart(
                x_data=data.x_values,
                y_data=data.y_values,
                title=config.title or "",
                xlabel=config.x_axis_label or "",
                ylabel=config.y_axis_label or "",
                show_legend=config.show_legend,
                show_grid=config.show_grid,
                figsize=(config.width / 100, config.height / 100),
            )
        elif chart_type == "bar":
            fig = self.render_bar_chart(
                x_data=data.x_values,
                y_data=data.y_values,
                title=config.title or "",
                xlabel=config.x_axis_label or "",
                ylabel=config.y_axis_label or "",
                show_legend=config.show_legend,
                show_grid=config.show_grid,
                stacked=config.stacked,
                figsize=(config.width / 100, config.height / 100),
            )
        elif chart_type == "scatter":
            fig = self.render_scatter_plot(
                x_data=data.x_values,
                y_data=list(data.y_values.values())[0] if data.y_values else [],
                title=config.title or "",
                xlabel=config.x_axis_label or "",
                ylabel=config.y_axis_label or "",
                show_grid=config.show_grid,
                figsize=(config.width / 100, config.height / 100),
            )
        elif chart_type == "heatmap":
            fig = self.render_heatmap(
                data=list(data.y_values.values()),
                x_labels=data.x_values,
                title=config.title or "",
                figsize=(config.width / 100, config.height / 100),
            )
        else:
            fig = self.render_line_chart(
                x_data=data.x_values,
                y_data=data.y_values,
                title=config.title or "",
                figsize=(config.width / 100, config.height / 100),
            )
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        config_hash = hashlib.md5(str(config.id).encode()).hexdigest()[:8]
        filename = f"chart_{timestamp}_{config_hash}.{export_format}"
        
        # Save file
        filepath = Path(settings.GENERATED_CHARTS_PATH) / str(config.user_id) / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        self.save_figure(fig, filepath, format=export_format)
        
        self.close_figure(fig)
        
        return {
            "file_path": str(filepath),
            "file_name": filename,
            "file_size": filepath.stat().st_size,
            "mime_type": f"image/{export_format}",
        }
    
    async def render_preview(self, config: Any, data: Any) -> bytes:
        """
        Render a quick preview of the chart.
        
        Args:
            config: Chart configuration
            data: Processed chart data
        
        Returns:
            Image bytes
        """
        fig = self.render_line_chart(
            x_data=data.x_values,
            y_data=data.y_values,
            title=config.title or "",
            figsize=(6, 4),
        )
        
        img_bytes = self.figure_to_bytes(fig, format="png", dpi=72)
        self.close_figure(fig)
        
        return img_bytes