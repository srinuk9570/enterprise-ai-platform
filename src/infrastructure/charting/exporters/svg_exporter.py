"""
SVG exporter for charts.
"""
import io
from pathlib import Path
from typing import Optional, Tuple, Union
from matplotlib.figure import Figure


class SVGExporter:
    """
    Export charts to SVG format (vector graphics).
    """
    
    def __init__(self, dpi: int = 150, metadata: Optional[dict] = None):
        self.dpi = dpi
        self.metadata = metadata or {}
    
    def export(
        self,
        fig: Figure,
        filepath: Optional[Union[str, Path]] = None,
        dpi: Optional[int] = None,
        bbox_inches: str = "tight",
        pad_inches: float = 0.1,
    ) -> Tuple[str, Optional[Path]]:
        """
        Export figure to SVG.
        
        Args:
            fig: Matplotlib figure
            filepath: Optional output path
            dpi: Resolution
            bbox_inches: Bounding box
            pad_inches: Padding
        
        Returns:
            Tuple of (svg_string, filepath)
        """
        dpi = dpi or self.dpi
        
        # Save to string buffer
        buf = io.StringIO()
        fig.savefig(
            buf,
            format='svg',
            dpi=dpi,
            bbox_inches=bbox_inches,
            pad_inches=pad_inches,
            facecolor=fig.get_facecolor(),
            edgecolor='none',
            metadata=self.metadata,
        )
        svg_string = buf.getvalue()
        
        # Save to file if path provided
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_string)
        
        return svg_string, filepath
    
    def export_string(
        self,
        fig: Figure,
        dpi: Optional[int] = None,
    ) -> str:
        """
        Export figure to SVG string only.
        
        Args:
            fig: Matplotlib figure
            dpi: Resolution
        
        Returns:
            SVG string
        """
        svg_string, _ = self.export(fig, dpi=dpi)
        return svg_string
    
    def export_base64(
        self,
        fig: Figure,
        dpi: Optional[int] = None,
    ) -> str:
        """
        Export figure to base64 encoded SVG.
        
        Args:
            fig: Matplotlib figure
            dpi: Resolution
        
        Returns:
            Base64 encoded string
        """
        import base64
        
        svg_string = self.export_string(fig, dpi)
        return base64.b64encode(svg_string.encode('utf-8')).decode('utf-8')
    
    def export_data_uri(
        self,
        fig: Figure,
        dpi: Optional[int] = None,
    ) -> str:
        """
        Export figure as data URI.
        
        Args:
            fig: Matplotlib figure
            dpi: Resolution
        
        Returns:
            Data URI string
        """
        import urllib.parse
        
        svg_string = self.export_string(fig, dpi)
        encoded = urllib.parse.quote(svg_string)
        return f"data:image/svg+xml;charset=utf-8,{encoded}"
    
    def optimize_svg(self, svg_string: str) -> str:
        """
        Optimize SVG string by removing unnecessary elements.
        
        Args:
            svg_string: Raw SVG string
        
        Returns:
            Optimized SVG string
        """
        import re
        
        # Remove comments
        svg_string = re.sub(r'<!--.*?-->', '', svg_string, flags=re.DOTALL)
        
        # Remove empty groups
        svg_string = re.sub(r'<g[^>]*>\s*</g>', '', svg_string)
        
        # Collapse whitespace
        svg_string = re.sub(r'>\s+<', '><', svg_string)
        
        return svg_string