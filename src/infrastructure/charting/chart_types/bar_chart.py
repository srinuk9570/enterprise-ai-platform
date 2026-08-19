"""
Bar chart implementation.
"""
import numpy as np
from typing import Optional, List, Union, Dict, Any
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from src.infrastructure.charting.matplotlib_engine import MatplotlibEngine


class BarChart:
    """
    Bar chart generator with grouped and stacked variants.
    """
    
    def __init__(self, engine: Optional[MatplotlibEngine] = None):
        self.engine = engine or MatplotlibEngine()
    
    def render(
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
        show_values: bool = False,
        value_format: str = "{:.1f}",
        **kwargs,
    ) -> Figure:
        """
        Render a bar chart.
        
        Args:
            x_data: Category labels
            y_data: Bar values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_legend: Display legend
            show_grid: Display grid
            stacked: Stack bars instead of grouping
            horizontal: Horizontal orientation
            bar_width: Width of bars
            show_values: Display value labels on bars
            value_format: Format for value labels
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        x_pos = np.arange(len(x_data))
        
        if isinstance(y_data, dict):
            if stacked:
                self._render_stacked_bars(
                    ax, x_pos, y_data, bar_width, horizontal,
                    show_values, value_format,
                )
            else:
                self._render_grouped_bars(
                    ax, x_pos, x_data, y_data, bar_width, horizontal,
                    show_values, value_format,
                )
        else:
            bar_func = ax.barh if horizontal else ax.bar
            bars = bar_func(
                x_pos,
                y_data,
                width=bar_width if horizontal else None,
                height=bar_width if not horizontal else None,
            )
            
            if show_values:
                self._add_value_labels(ax, bars, horizontal, value_format)
        
        self._setup_axes(
            ax, x_pos, x_data, title, xlabel, ylabel, horizontal,
        )
        
        if show_legend and isinstance(y_data, dict):
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        ax.grid(show_grid, axis='y' if not horizontal else 'x', alpha=0.3, linestyle='--')
        
        fig.tight_layout()
        
        return fig
    
    def render_comparison(
        self,
        categories: List[str],
        series_a: List[float],
        series_b: List[float],
        label_a: str = "Series A",
        label_b: str = "Series B",
        title: str = "",
        **kwargs,
    ) -> Figure:
        """
        Render a comparison bar chart (side-by-side).
        
        Args:
            categories: Category labels
            series_a: First series values
            series_b: Second series values
            label_a: Label for first series
            label_b: Label for second series
            title: Chart title
        
        Returns:
            Matplotlib Figure
        """
        return self.render(
            x_data=categories,
            y_data={label_a: series_a, label_b: series_b},
            title=title,
            **kwargs,
        )
    
    def render_diverging(
        self,
        categories: List[str],
        values: List[float],
        title: str = "",
        positive_color: str = "#00d2ff",
        negative_color: str = "#ef4444",
        **kwargs,
    ) -> Figure:
        """
        Render a diverging bar chart (positive/negative).
        
        Args:
            categories: Category labels
            values: Values (can be negative)
            title: Chart title
            positive_color: Color for positive values
            negative_color: Color for negative values
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        colors = [positive_color if v >= 0 else negative_color for v in values]
        
        y_pos = np.arange(len(categories))
        ax.barh(y_pos, values, color=colors)
        ax.axvline(x=0, color='white', linewidth=1, alpha=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')
        
        fig.tight_layout()
        
        return fig
    
    def _render_stacked_bars(
        self,
        ax,
        x_pos: np.ndarray,
        y_data: Dict[str, Union[List, np.ndarray]],
        bar_width: float,
        horizontal: bool,
        show_values: bool,
        value_format: str,
    ) -> None:
        """Render stacked bars."""
        bottom = np.zeros(len(x_pos))
        
        for label, data in y_data.items():
            bar_func = ax.barh if horizontal else ax.bar
            
            if horizontal:
                bars = bar_func(
                    x_pos, data,
                    height=bar_width,
                    left=bottom,
                    label=label,
                )
            else:
                bars = bar_func(
                    x_pos, data,
                    width=bar_width,
                    bottom=bottom,
                    label=label,
                )
            
            if show_values:
                self._add_stacked_value_labels(
                    ax, bars, bottom, horizontal, value_format,
                )
            
            bottom += np.array(data)
    
    def _render_grouped_bars(
        self,
        ax,
        x_pos: np.ndarray,
        x_data: List,
        y_data: Dict[str, Union[List, np.ndarray]],
        bar_width: float,
        horizontal: bool,
        show_values: bool,
        value_format: str,
    ) -> None:
        """Render grouped bars."""
        n_series = len(y_data)
        bar_width_adjusted = bar_width / n_series
        
        for i, (label, data) in enumerate(y_data.items()):
            offset = (i - n_series / 2 + 0.5) * bar_width_adjusted
            bar_func = ax.barh if horizontal else ax.bar
            
            if horizontal:
                bars = bar_func(
                    x_pos + offset,
                    data,
                    height=bar_width_adjusted,
                    label=label,
                )
            else:
                bars = bar_func(
                    x_pos + offset,
                    data,
                    width=bar_width_adjusted,
                    label=label,
                )
            
            if show_values:
                self._add_value_labels(ax, bars, horizontal, value_format)
    
    def _setup_axes(
        self,
        ax,
        x_pos: np.ndarray,
        x_data: List,
        title: str,
        xlabel: str,
        ylabel: str,
        horizontal: bool,
    ) -> None:
        """Setup axes ticks and labels."""
        if horizontal:
            ax.set_yticks(x_pos)
            ax.set_yticklabels(x_data)
            ax.set_xlabel(ylabel, fontsize=12)
            ax.set_ylabel(xlabel, fontsize=12)
        else:
            ax.set_xticks(x_pos)
            ax.set_xticklabels(x_data, rotation=45, ha='right')
            ax.set_xlabel(xlabel, fontsize=12)
            ax.set_ylabel(ylabel, fontsize=12)
        
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
    
    def _add_value_labels(
        self,
        ax,
        bars,
        horizontal: bool,
        value_format: str,
    ) -> None:
        """Add value labels on bars."""
        for bar in bars:
            if horizontal:
                width = bar.get_width()
                ax.text(
                    width + (width * 0.01),
                    bar.get_y() + bar.get_height() / 2,
                    value_format.format(width),
                    ha='left', va='center',
                    fontsize=9,
                )
            else:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + (height * 0.01),
                    value_format.format(height),
                    ha='center', va='bottom',
                    fontsize=9,
                )
    
    def _add_stacked_value_labels(
        self,
        ax,
        bars,
        bottom: np.ndarray,
        horizontal: bool,
        value_format: str,
    ) -> None:
        """Add value labels for stacked bars."""
        for i, bar in enumerate(bars):
            if horizontal:
                width = bar.get_width()
                if width > 0:
                    center = bottom[i] + width / 2
                    ax.text(
                        center,
                        bar.get_y() + bar.get_height() / 2,
                        value_format.format(width),
                        ha='center', va='center',
                        fontsize=9,
                    )
            else:
                height = bar.get_height()
                if height > 0:
                    center = bottom[i] + height / 2
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        center,
                        value_format.format(height),
                        ha='center', va='center',
                        fontsize=9,
                    )