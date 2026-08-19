"""
PNG exporter for charts.
"""
import io
from pathlib import Path
from typing import Optional, Tuple, Union
from matplotlib.figure import Figure


class PNGExporter:
    """
    Export charts to PNG format.
    """
    
    def __init__(self, dpi: int = 150, transparent: bool = False):
        self.dpi = dpi
        self.transparent = transparent
    
    def export(
        self,
        fig: Figure,
        filepath: Optional[Union[str, Path]] = None,
        dpi: Optional[int] = None,
        bbox_inches: str = "tight",
        pad_inches: float = 0.1,
    ) -> Tuple[bytes, Optional[Path]]:
        """
        Export figure to PNG.
        
        Args:
            fig: Matplotlib figure
            filepath: Optional output path
            dpi: Resolution (overrides default)
            bbox_inches: Bounding box
            pad_inches: Padding
        
        Returns:
            Tuple of (bytes, filepath)
        """
        dpi = dpi or self.dpi
        
        # Save to bytes
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            dpi=dpi,
            bbox_inches=bbox_inches,
            pad_inches=pad_inches,
            transparent=self.transparent,
            facecolor=fig.get_facecolor(),
            edgecolor='none',
        )
        buf.seek(0)
        img_bytes = buf.getvalue()
        
        # Save to file if path provided
        if filepath:
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                f.write(img_bytes)
        
        return img_bytes, filepath
    
    def export_bytes(
        self,
        fig: Figure,
        dpi: Optional[int] = None,
    ) -> bytes:
        """
        Export figure to PNG bytes only.
        
        Args:
            fig: Matplotlib figure
            dpi: Resolution
        
        Returns:
            PNG bytes
        """
        img_bytes, _ = self.export(fig, dpi=dpi)
        return img_bytes
    
    def export_base64(
        self,
        fig: Figure,
        dpi: Optional[int] = None,
    ) -> str:
        """
        Export figure to base64 encoded PNG.
        
        Args:
            fig: Matplotlib figure
            dpi: Resolution
        
        Returns:
            Base64 encoded string
        """
        import base64
        
        img_bytes = self.export_bytes(fig, dpi)
        return base64.b64encode(img_bytes).decode('utf-8')
    
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
        base64_str = self.export_base64(fig, dpi)
        return f"data:image/png;base64,{base64_str}"