"""
Scatter plot implementation.
"""
import numpy as np
from typing import Optional, List, Union, Dict, Any
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from src.infrastructure.charting.matplotlib_engine import MatplotlibEngine


class ScatterPlot:
    """
    Scatter plot generator with regression and clustering support.
    """
    
    def __init__(self, engine: Optional[MatplotlibEngine] = None):
        self.engine = engine or MatplotlibEngine()
    
    def render(
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
        colorbar_label: Optional[str] = None,
        **kwargs,
    ) -> Figure:
        """
        Render a scatter plot.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            show_grid: Display grid
            color: Point color(s) - can be values for colormap
            size: Point size(s) - can be values for size mapping
            alpha: Point transparency
            colorbar_label: Label for colorbar
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        scatter_kwargs = {
            'alpha': alpha,
            'edgecolors': 'white',
            'linewidth': 0.5,
        }
        
        if color is not None:
            scatter_kwargs['c'] = color
            scatter_kwargs['cmap'] = kwargs.get('cmap', 'viridis')
        
        if size is not None:
            if isinstance(size, (int, float)):
                scatter_kwargs['s'] = size
            else:
                # Normalize size to reasonable range
                size_array = np.array(size)
                normalized = 20 + 200 * (size_array - size_array.min()) / (size_array.max() - size_array.min() + 1e-10)
                scatter_kwargs['s'] = normalized
        
        scatter = ax.scatter(x_data, y_data, **scatter_kwargs)
        
        if color is not None and isinstance(color, (list, np.ndarray)) and colorbar_label:
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label(colorbar_label)
        
        self._apply_labels(ax, title, xlabel, ylabel)
        ax.grid(show_grid, alpha=0.3, linestyle='--')
        
        fig.tight_layout()
        
        return fig
    
    def render_with_regression(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray],
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        degree: int = 1,
        show_equation: bool = True,
        show_r2: bool = True,
        **kwargs,
    ) -> Figure:
        """
        Render scatter plot with regression line.
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
            degree: Polynomial degree for regression
            show_equation: Display regression equation
            show_r2: Display R-squared value
        
        Returns:
            Matplotlib Figure
        """
        from sklearn.linear_model import LinearRegression
        from sklearn.preprocessing import PolynomialFeatures
        from sklearn.metrics import r2_score
        
        fig, ax = self.engine.create_figure(**kwargs)
        
        x_array = np.array(x_data).reshape(-1, 1)
        y_array = np.array(y_data)
        
        # Scatter points
        ax.scatter(x_data, y_data, alpha=0.6, edgecolors='white', linewidth=0.5)
        
        # Regression
        if degree == 1:
            model = LinearRegression()
            model.fit(x_array, y_array)
            y_pred = model.predict(x_array)
            coef = model.coef_[0]
            intercept = model.intercept_
            equation = f"y = {coef:.3f}x + {intercept:.3f}"
        else:
            poly = PolynomialFeatures(degree=degree)
            x_poly = poly.fit_transform(x_array)
            model = LinearRegression()
            model.fit(x_poly, y_array)
            
            x_smooth = np.linspace(x_array.min(), x_array.max(), 100).reshape(-1, 1)
            x_smooth_poly = poly.transform(x_smooth)
            y_pred = model.predict(x_smooth_poly)
            x_array = x_smooth.flatten()
            
            equation = f"Polynomial (degree {degree})"
        
        r2 = r2_score(y_array, model.predict(poly.transform(x_array.reshape(-1, 1)) if degree > 1 else x_array.reshape(-1, 1)))
        
        # Plot regression line
        ax.plot(x_array, y_pred if degree == 1 else y_pred, color='red', linewidth=2, label='Regression')
        
        # Add equation text
        if show_equation or show_r2:
            text = ""
            if show_equation:
                text += equation
            if show_r2:
                if text:
                    text += "\n"
                text += f"R² = {r2:.4f}"
            
            ax.text(
                0.05, 0.95, text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
            )
        
        self._apply_labels(ax, title, xlabel, ylabel)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        return fig
    
    def render_bubble_chart(
        self,
        x_data: Union[List, np.ndarray],
        y_data: Union[List, np.ndarray],
        size_data: Union[List, np.ndarray],
        color_data: Optional[Union[List, np.ndarray]] = None,
        labels: Optional[List[str]] = None,
        title: str = "",
        xlabel: str = "",
        ylabel: str = "",
        **kwargs,
    ) -> Figure:
        """
        Render a bubble chart (scatter with sized points).
        
        Args:
            x_data: X-axis values
            y_data: Y-axis values
            size_data: Bubble sizes
            color_data: Bubble colors
            labels: Point labels
            title: Chart title
            xlabel: X-axis label
            ylabel: Y-axis label
        
        Returns:
            Matplotlib Figure
        """
        fig, ax = self.engine.create_figure(**kwargs)
        
        scatter = ax.scatter(
            x_data, y_data,
            s=size_data,
            c=color_data if color_data is not None else self.engine.theme.primary_color,
            alpha=0.6,
            edgecolors='white',
            linewidth=0.5,
            cmap=kwargs.get('cmap', 'viridis'),
        )
        
        if color_data is not None:
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label(kwargs.get('colorbar_label', ''))
        
        if labels:
            for i, label in enumerate(labels):
                ax.annotate(
                    label,
                    (x_data[i], y_data[i]),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    alpha=0.8,
                )
        
        self._apply_labels(ax, title, xlabel, ylabel)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        return fig
    
    def _apply_labels(self, ax, title: str, xlabel: str, ylabel: str) -> None:
        """Apply labels to axes."""
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)