"""
Light theme for charts.
"""
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt

from src.infrastructure.charting.themes.base_theme import ChartTheme


class LightTheme(ChartTheme):
    """
    Light theme for presentations and printing.
    """
    
    @property
    def name(self) -> str:
        return "light"
    
    @property
    def background_color(self) -> str:
        return "#ffffff"
    
    @property
    def figure_facecolor(self) -> str:
        return "#ffffff"
    
    @property
    def axes_facecolor(self) -> str:
        return "#f8f9fa"
    
    @property
    def text_color(self) -> str:
        return "#212529"
    
    @property
    def grid_color(self) -> str:
        return "#dee2e6"
    
    @property
    def spine_color(self) -> str:
        return "#ced4da"
    
    @property
    def primary_color(self) -> str:
        return "#0066cc"
    
    @property
    def secondary_color(self) -> str:
        return "#6c47ff"
    
    @property
    def accent_color(self) -> str:
        return "#d97706"
    
    @property
    def color_palette(self) -> list:
        return [
            "#0066cc",  # Blue
            "#6c47ff",  # Purple
            "#d97706",  # Amber
            "#059669",  # Emerald
            "#dc2626",  # Red
            "#2563eb",  # Blue dark
            "#db2777",  # Pink
            "#0891b2",  # Cyan
            "#ea580c",  # Orange
            "#7c3aed",  # Violet
        ]
    
    def apply(self, ax: Axes, fig: Figure = None) -> None:
        """Apply light theme to axes and figure."""
        # Figure settings
        if fig:
            fig.patch.set_facecolor(self.figure_facecolor)
        
        # Axes settings
        ax.set_facecolor(self.axes_facecolor)
        
        # Spine colors
        for spine in ax.spines.values():
            spine.set_color(self.spine_color)
            spine.set_linewidth(0.8)
        
        # Tick colors
        ax.tick_params(colors=self.text_color, labelsize=10)
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)
        
        # Title color
        ax.title.set_color(self.text_color)
        
        # Grid
        ax.grid(True, color=self.grid_color, alpha=0.5, linestyle='--', linewidth=0.5)
        
        # Legend
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(self.figure_facecolor)
            legend.get_frame().set_edgecolor(self.spine_color)
            legend.get_frame().set_alpha(0.95)
            for text in legend.get_texts():
                text.set_color(self.text_color)
        
        # Style existing lines
        for line in ax.get_lines():
            if line.get_color() in ['b', 'blue', '#1f77b4']:
                line.set_color(self.primary_color)