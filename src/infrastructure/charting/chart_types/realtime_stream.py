"""
Real-time streaming chart implementation.
"""
import numpy as np
import asyncio
import time
from typing import Optional, List, Dict, Any, AsyncGenerator, Callable
from collections import deque
from datetime import datetime
import io
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from src.infrastructure.charting.matplotlib_engine import MatplotlibEngine


class RealtimeStream:
    """
    Real-time streaming chart with fixed buffer size.
    """
    
    def __init__(
        self,
        engine: Optional[MatplotlibEngine] = None,
        buffer_size: int = 100,
        update_interval_ms: int = 500,
    ):
        self.engine = engine or MatplotlibEngine()
        self.buffer_size = buffer_size
        self.update_interval = update_interval_ms / 1000
        
        self._data_buffers: Dict[str, deque] = {}
        self._time_buffer: deque = deque(maxlen=buffer_size)
        self._is_running = False
        self._fig: Optional[Figure] = None
        self._ax = None
    
    def add_data_source(self, name: str) -> None:
        """Add a new data series."""
        self._data_buffers[name] = deque(maxlen=self.buffer_size)
    
    def add_data_point(self, name: str, value: float) -> None:
        """
        Add a single data point.
        
        Args:
            name: Series name
            value: Data value
        """
        if name not in self._data_buffers:
            self.add_data_source(name)
        
        self._data_buffers[name].append(value)
        
        # Add timestamp if this is the first series being updated
        if len(self._time_buffer) == 0 or name == list(self._data_buffers.keys())[0]:
            self._time_buffer.append(datetime.utcnow())
    
    def add_batch(
        self,
        data: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add a batch of data points.
        
        Args:
            data: Dictionary of series name to value
            timestamp: Optional timestamp
        """
        for name, value in data.items():
            self.add_data_point(name, value)
        
        if timestamp:
            self._time_buffer.append(timestamp)
        else:
            self._time_buffer.append(datetime.utcnow())
    
    def get_current_data(self) -> Dict[str, List[float]]:
        """Get current buffered data."""
        return {
            name: list(buffer)
            for name, buffer in self._data_buffers.items()
        }
    
    def render_frame(self) -> bytes:
        """
        Render current frame as PNG bytes.
        
        Returns:
            PNG image bytes
        """
        if self._fig is None or self._ax is None:
            self._fig, self._ax = self.engine.create_figure(figsize=(10, 6))
        
        self._ax.clear()
        
        # Plot each series
        x_values = list(range(len(self._time_buffer)))
        
        for name, buffer in self._data_buffers.items():
            if buffer:
                y_values = list(buffer)
                x_plot = x_values[-len(y_values):]
                self._ax.plot(x_plot, y_values, label=name, linewidth=2)
        
        self._ax.set_title("Real-time Data Stream", fontsize=14, fontweight='bold')
        self._ax.set_xlabel("Time", fontsize=12)
        self._ax.set_ylabel("Value", fontsize=12)
        
        if len(self._data_buffers) > 1:
            self._ax.legend(loc='best')
        
        self._ax.grid(True, alpha=0.3, linestyle='--')
        
        # Set x-tick labels as timestamps
        if self._time_buffer:
            step = max(1, len(self._time_buffer) // 10)
            tick_positions = range(0, len(self._time_buffer), step)
            tick_labels = [
                list(self._time_buffer)[i].strftime("%H:%M:%S")
                for i in tick_positions
            ]
            self._ax.set_xticks(tick_positions)
            self._ax.set_xticklabels(tick_labels, rotation=45, ha='right')
        
        self._fig.tight_layout()
        
        # Convert to bytes
        buf = io.BytesIO()
        self._fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        return buf.getvalue()
    
    async def stream_frames(self) -> AsyncGenerator[bytes, None]:
        """
        Stream frames as they are generated.
        
        Yields:
            PNG image bytes
        """
        self._is_running = True
        
        while self._is_running:
            if any(buffer for buffer in self._data_buffers.values()):
                yield self.render_frame()
            
            await asyncio.sleep(self.update_interval)
    
    def stop(self) -> None:
        """Stop streaming."""
        self._is_running = False
        
        if self._fig:
            plt.close(self._fig)
            self._fig = None
            self._ax = None
    
    def clear(self) -> None:
        """Clear all buffered data."""
        self._time_buffer.clear()
        for buffer in self._data_buffers.values():
            buffer.clear()
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for each series."""
        stats = {}
        
        for name, buffer in self._data_buffers.items():
            if buffer:
                values = list(buffer)
                stats[name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "mean": sum(values) / len(values),
                    "last": values[-1] if values else None,
                }
        
        return stats
    
    async def stream_from_generator(
        self,
        generator: AsyncGenerator[Dict[str, float], None],
        frame_callback: Optional[Callable[[bytes], None]] = None,
    ) -> None:
        """
        Stream data from an async generator.
        
        Args:
            generator: Async generator yielding data points
            frame_callback: Optional callback for each frame
        """
        self._is_running = True
        
        async for data_point in generator:
            if not self._is_running:
                break
            
            self.add_batch(data_point)
            frame = self.render_frame()
            
            if frame_callback:
                frame_callback(frame)
        
        self.stop()
    
    def stream_from_sync_generator(
        self,
        generator: Callable[[], Dict[str, float]],
        max_iterations: Optional[int] = None,
    ) -> None:
        """
        Stream data from a sync generator function.
        
        Args:
            generator: Function returning data points
            max_iterations: Maximum iterations (None for infinite)
        """
        import time
        
        self._is_running = True
        iteration = 0
        
        while self._is_running:
            if max_iterations and iteration >= max_iterations:
                break
            
            try:
                data_point = generator()
                self.add_batch(data_point)
                iteration += 1
            except StopIteration:
                break
            
            time.sleep(self.update_interval)
        
        self.stop()