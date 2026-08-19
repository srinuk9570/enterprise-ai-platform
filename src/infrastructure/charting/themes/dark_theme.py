"""
Dark theme for charts.
"""
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt

from src.infrastructure.charting.themes.base_theme import ChartTheme


class DarkTheme(ChartTheme):
    """
    Dark theme optimized for low-light environments.
    """
    
    @property
    def name(self) -> str:
        return "dark"
    
    @property
    def background_color(self) -> str:
        return "#1a1a2e"
    
    @property
    def figure_facecolor(self) -> str:
        return "#1a1a2e"
    
    @property
    def axes_facecolor(self) -> str:
        return "#0e1117"
    
    @property
    def text_color(self) -> str:
        return "#ffffff"
    
    @property
    def grid_color(self) -> str:
        return "#3d3d5c"
    
    @property
    def spine_color(self) -> str:
        return "#4a4a6a"
    
    @property
    def primary_color(self) -> str:
        return "#00d2ff"
    
    @property
    def secondary_color(self) -> str:
        return "#7c3aed"
    
    @property
    def accent_color(self) -> str:
        return "#f59e0b"
    
    @property
    def color_palette(self) -> list:
        return [
            "#00d2ff",  # Cyan
            "#7c3aed",  # Purple
            "#f59e0b",  # Amber
            "#10b981",  # Emerald
            "#ef4444",  # Red
            "#3b82f6",  # Blue
            "#ec4899",  # Pink
            "#06b6d4",  # Cyan dark
            "#f97316",  # Orange
            "#8b5cf6",  # Violet
        ]
    
    def apply(self, ax: Axes, fig: Figure = None) -> None:
        """Apply dark theme to axes and figure."""
        # Figure settings
        if fig:
            fig.patch.set_facecolor(self.figure_facecolor)
        
        # Axes settings
        ax.set_facecolor(self.axes_facecolor)
        
        # Spine colors
        for spine in ax.spines.values():
            spine.set_color(self.spine_color)
            spine.set_linewidth(0.5)
        
        # Tick colors
        ax.tick_params(colors=self.text_color, labelsize=10)
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)
        
        # Title color
        ax.title.set_color(self.text_color)
        
        # Grid
        ax.grid(True, color=self.grid_color, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Legend
        legend = ax.get_legend()
        if legend:
            legend.get_frame().set_facecolor(self.figure_facecolor)
            legend.get_frame().set_edgecolor(self.spine_color)
            legend.get_frame().set_alpha(0.9)
            for text in legend.get_texts():
                text.set_color(self.text_color)
        
        # Style existing lines
        for line in ax.get_lines():
            if line.get_color() in ['b', 'blue', '#1f77b4']:
                line.set_color(self.primary_color)