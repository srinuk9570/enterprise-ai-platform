"""
Base chart theme abstract class.
"""
from abc import ABC, abstractmethod
from matplotlib.figure import Figure
from matplotlib.axes import Axes


class ChartTheme(ABC):
    """
    Abstract base class for chart themes.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Theme name."""
        pass
    
    @property
    @abstractmethod
    def background_color(self) -> str:
        """Background color."""
        pass
    
    @property
    @abstractmethod
    def figure_facecolor(self) -> str:
        """Figure face color."""
        pass
    
    @property
    @abstractmethod
    def axes_facecolor(self) -> str:
        """Axes face color."""
        pass
    
    @property
    @abstractmethod
    def text_color(self) -> str:
        """Text color."""
        pass
    
    @property
    @abstractmethod
    def grid_color(self) -> str:
        """Grid line color."""
        pass
    
    @property
    @abstractmethod
    def spine_color(self) -> str:
        """Spine color."""
        pass
    
    @property
    @abstractmethod
    def primary_color(self) -> str:
        """Primary accent color."""
        pass
    
    @property
    @abstractmethod
    def secondary_color(self) -> str:
        """Secondary accent color."""
        pass
    
    @property
    @abstractmethod
    def accent_color(self) -> str:
        """Accent color for highlights."""
        pass
    
    @property
    @abstractmethod
    def color_palette(self) -> list:
        """Color palette for multiple series."""
        pass
    
    @abstractmethod
    def apply(self, ax: Axes, fig: Figure = None) -> None:
        """
        Apply theme to axes and figure.
        
        Args:
            ax: Matplotlib axes
            fig: Optional Matplotlib figure
        """
        pass
    
    def get_color(self, index: int) -> str:
        """
        Get color from palette by index.
        
        Args:
            index: Color index
        
        Returns:
            Hex color string
        """
        palette = self.color_palette
        return palette[index % len(palette)]