"""
Line chart implementation.
"""
import numpy as np
from typing import Optional, List, Union, Dict, Any
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from src.infrastructure.charting.matplotlib_engine import MatplotlibEngine
from src.infrastructure.charting.themes import ChartTheme, DarkTheme


class LineChart:
    """
    Line chart generator with advanced features.
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
        line_width: float = 2.0,
        markers: bool = False,
        fill_between: bool = False,
        smooth: bool = False,
        **kwargs,
    ) -> Figure:
        """
        Render a line chart.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values (single series or dict of named series)
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_legend: Display legend
            show_grid: Display grid
            line_width: Width of lines
            markers: Show data point markers
            fill_between: Fill area under line
            smooth: Apply smoothing
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        if smooth:
            y_data = self._smooth_data(y_data)
        
        if isinstance(y_data, dict):
            for label, data in y_data.items():
                line = ax.plot(
                    x_data, data,
                    label=label,
                    linewidth=line_width,
                    marker='o' if markers else None,
                    markersize=4 if markers else None,
                )
                
                if fill_between:
                    ax.fill_between(
                        x_data, data,
                        alpha=0.3,
                        color=line[0].get_color(),
                    )
        else:
            line = ax.plot(
                x_data, y_data,
                linewidth=line_width,
                marker='o' if markers else None,
                markersize=4 if markers else None,
            )
            
            if fill_between:
                ax.fill_between(
                    x_data, y_data,
                    alpha=0.3,
                    color=line[0].get_color(),
                )
        
        self._apply_labels(ax, title, xlabel, ylabel)
        
        if show_legend and isinstance(y_data, dict):
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
        ax.grid(show_grid, alpha=0.3, linestyle='--')
        
        fig.tight_layout()
        
        return fig
    
    def render_with_confidence(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray],
        y_std: Union[List, np.ndarray],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        confidence: float = 0.95,
        **kwargs,
    ) -> Figure:
        """
        Render line chart with confidence interval.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            y_std: Standard deviation
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            confidence: Confidence level
        
        Returns:
            Matplotlib Figure
        """
        from scipy import stats
        
        fig, ax = self.engine.create_figure(**kwargs)
        
        z_score = stats.norm.ppf((1 + confidence) / 2)
        
        y_data = np.array(y_data)
        y_std = np.array(y_std)
        
        ax.plot(x_data, y_data, linewidth=2, label='Mean')
        ax.fill_between(
            x_data,
            y_data - z_score * y_std,
            y_data + z_score * y_std,
            alpha=0.3,
            label=f'{confidence*100:.0f}% CI',
        )
        
        self._apply_labels(ax, title, xlabel, ylabel)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def render_with_trend(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray],
        trend_window: int = 7,
        **kwargs,
    ) -> Figure:
        """
        Render line chart with moving average trend line.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            trend_window: Window size for moving average
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        ax.plot(x_data, y_data, linewidth=1.5, alpha=0.7, label='Original')
        
        # Calculate moving average
        y_array = np.array(y_data)
        moving_avg = np.convolve(y_array, np.ones(trend_window)/trend_window, mode='valid')
        x_ma = x_data[trend_window-1:]
        
        ax.plot(x_ma, moving_avg, linewidth=2.5, label=f'{trend_window}-period MA', color='red')
        
        self._apply_labels(ax, kwargs.get('title', ''), kwargs.get('xlabel', ''), kwargs.get('ylabel', ''))
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        return fig
    
    def _smooth_data(
        self,
        data: Union[List, np.ndarray, Dict[str, Union[List, np.ndarray]]],
        window: int = 5,
    ) -> Union[np.ndarray, Dict[str, np.ndarray]]:
        """Apply moving average smoothing."""
        if isinstance(data, dict):
            return {
                label: self._smooth_array(np.array(values), window)
                for label, values in data.items()
            }
        else:
            return self._smooth_array(np.array(data), window)
    
    def _smooth_array(self, arr: np.ndarray, window: int) -> np.ndarray:
        """Smooth a single array."""
        if len(arr) < window:
            return arr
        return np.convolve(arr, np.ones(window)/window, mode='same')
    
    def _apply_labels(self, ax, title: str, xlabel: str, ylabel: str) -> None:
        """Apply labels to axes."""
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)