"""
WebSocket handler for real-time chart data streaming.
"""
import logging
import json
import asyncio
from typing import Optional, Dict, Any, List
from uuid import UUID
import numpy as np
from datetime import datetime
from fastapi import WebSocket

from src.presentation.websocket.handlers.base_handler import BaseWebSocketHandler
from src.presentation.websocket.connection_manager import ConnectionManager
from src.presentation.websocket.events.event_types import EventType, WebSocketEvent
from src.presentation.api.dependencies import get_dependencies

logger = logging.getLogger(__name__)


class ChartStreamHandler(BaseWebSocketHandler):
    """
    Handler for streaming real-time chart data.
    """
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        super().__init__(connection_manager)
        self._active_streams: Dict[str, asyncio.Task] = {}
        self._data_buffers: Dict[str, List[float]] = {}
    
    def _setup_handlers(self) -> None:
        """Setup chart-specific handlers."""
        super()._setup_handlers()
        
        self._handlers.update({
            EventType.CHART_DATA: self._handle_chart_data,
            EventType.STREAM_START: self._handle_stream_start,
            EventType.STREAM_STOP: self._handle_stream_stop,
            EventType.CHART_UPDATE: self._handle_chart_update,
        })
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        chart_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle a chart streaming WebSocket connection.
        """
        room = f"chart:{chart_id}" if chart_id else f"chart_user:{user_id}"
        
        metadata = metadata or {}
        metadata["chart_id"] = chart_id
        
        await super().handle_connection(websocket, user_id, room, metadata)
    
    async def _handle_chart_data(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Handle incoming chart data point.
        """
        chart_id = data.get("chart_id")
        value = data.get("value")
        timestamp = data.get("timestamp")
        
        if chart_id and value is not None:
            # Store in buffer
            buffer_key = f"{chart_id}_{user_id}"
            
            if buffer_key not in self._data_buffers:
                self._data_buffers[buffer_key] = []
            
            self._data_buffers[buffer_key].append({
                "value": float(value),
                "timestamp": timestamp or datetime.utcnow().isoformat(),
            })
            
            # Keep buffer size reasonable
            if len(self._data_buffers[buffer_key]) > 1000:
                self._data_buffers[buffer_key] = self._data_buffers[buffer_key][-500:]
    
    async def _handle_chart_update(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Handle chart update request.
        """
        chart_id = data.get("chart_id")
        
        if chart_id:
            buffer_key = f"{chart_id}_{user_id}"
            
            if buffer_key in self._data_buffers:
                # Send buffered data
                await self.manager.send_personal_json(
                    WebSocketEvent(
                        type=EventType.CHART_UPDATE,
                        data={
                            "chart_id": chart_id,
                            "data": self._data_buffers[buffer_key],
                        },
                    ).to_dict(),
                    user_id,
                )
    
    async def _handle_stream_start(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Start streaming chart data.
        """
        chart_id = data.get("chart_id")
        interval_ms = data.get("interval_ms", 1000)
        data_source = data.get("data_source")
        chart_config = data.get("chart_config", {})
        
        if not chart_id:
            await self._send_error(websocket, "Missing chart_id")
            return
        
        stream_id = f"{chart_id}_{user_id}"
        
        # Cancel existing stream if any
        if stream_id in self._active_streams:
            self._active_streams[stream_id].cancel()
        
        # Clear old buffer
        buffer_key = f"{chart_id}_{user_id}"
        self._data_buffers[buffer_key] = []
        
        async def stream_task():
            try:
                deps = get_dependencies()
                
                await self.manager.send_personal_json(
                    WebSocketEvent(
                        type=EventType.STREAM_START,
                        data={"chart_id": chart_id, "interval_ms": interval_ms},
                    ).to_dict(),
                    user_id,
                )
                
                while True:
                    # Generate or fetch data point
                    if data_source == "random":
                        # Generate random data for demo
                        value = float(np.random.randn() * 10 + 50)
                    elif data_source == "sine":
                        # Generate sine wave
                        import math
                        t = len(self._data_buffers.get(buffer_key, []))
                        value = 50 + 20 * math.sin(t * 0.1)
                    elif data_source == "api":
                        # Fetch from API
                        try:
                            # Example: fetch from configured endpoint
                            pass
                        except Exception:
                            value = None
                    else:
                        # Use configured data source
                        value = None
                    
                    if value is not None:
                        point = {
                            "value": round(value, 2),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        
                        # Store in buffer
                        if buffer_key not in self._data_buffers:
                            self._data_buffers[buffer_key] = []
                        self._data_buffers[buffer_key].append(point)
                        
                        if len(self._data_buffers[buffer_key]) > 1000:
                            self._data_buffers[buffer_key] = self._data_buffers[buffer_key][-500:]
                        
                        # Send to client
                        await self.manager.send_personal_json(
                            WebSocketEvent.chart_update(
                                {"chart_id": chart_id, "point": point},
                                room,
                            ).to_dict(),
                            user_id,
                        )
                    
                    await asyncio.sleep(interval_ms / 1000)
                    
            except asyncio.CancelledError:
                logger.info(f"Chart stream {stream_id} cancelled")
                
                # Send final buffer
                if buffer_key in self._data_buffers:
                    await self.manager.send_personal_json(
                        WebSocketEvent(
                            type=EventType.STREAM_STOP,
                            data={
                                "chart_id": chart_id,
                                "data": self._data_buffers[buffer_key],
                            },
                        ).to_dict(),
                        user_id,
                    )
            except Exception as e:
                logger.error(f"Chart stream error: {e}")
                await self.manager.send_personal_json(
                    WebSocketEvent.error(str(e), "CHART_STREAM_ERROR").to_dict(),
                    user_id,
                )
            finally:
                self._active_streams.pop(stream_id, None)
        
        task = asyncio.create_task(stream_task())
        self._active_streams[stream_id] = task
    
    async def _handle_stream_stop(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Stop streaming chart data.
        """
        chart_id = data.get("chart_id")
        
        if not chart_id:
            await self._send_error(websocket, "Missing chart_id")
            return
        
        stream_id = f"{chart_id}_{user_id}"
        
        if stream_id in self._active_streams:
            self._active_streams[stream_id].cancel()
        else:
            await self.manager.send_personal_json(
                WebSocketEvent(
                    type=EventType.STREAM_STOP,
                    data={"chart_id": chart_id, "message": "No active stream"},
                ).to_dict(),
                user_id,
            )
    
    async def stream_live_data(
        self,
        chart_id: str,
        data_generator,
        interval_ms: int = 1000,
        room: Optional[str] = None,
    ) -> None:
        """
        Stream data from a generator to all subscribers.
        """
        room = room or f"chart:{chart_id}"
        
        async for data_point in data_generator:
            await self.manager.broadcast_json(
                WebSocketEvent.chart_update(
                    {"chart_id": chart_id, "point": data_point},
                    room,
                ).to_dict(),
                room=room,
            )
            await asyncio.sleep(interval_ms / 1000)
    
    async def broadcast_chart_generated(
        self,
        chart_id: str,
        asset_data: Dict[str, Any],
        room: Optional[str] = None,
    ) -> None:
        """
        Broadcast that a chart has been generated.
        """
        room = room or f"chart:{chart_id}"
        
        await self.manager.broadcast_json(
            WebSocketEvent(
                type=EventType.CHART_GENERATED,
                data={
                    "chart_id": chart_id,
                    "asset": asset_data,
                },
            ).to_dict(),
            room=room,
        )
    
    def stop_stream(self, chart_id: str, user_id: str) -> bool:
        """Stop a specific chart stream."""
        stream_id = f"{chart_id}_{user_id}"
        
        if stream_id in self._active_streams:
            self._active_streams[stream_id].cancel()
            return True
        return False
    
    def stop_all_streams(self, user_id: Optional[str] = None) -> int:
        """Stop all or user-specific streams."""
        stopped = 0
        
        for stream_id, task in list(self._active_streams.items()):
            if user_id is None or stream_id.endswith(f"_{user_id}"):
                task.cancel()
                stopped += 1
        
        return stopped
    
    def get_buffer_data(self, chart_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get buffered data for a chart."""
        buffer_key = f"{chart_id}_{user_id}"
        return self._data_buffers.get(buffer_key, [])
    
    def clear_buffer(self, chart_id: str, user_id: str) -> None:
        """Clear buffered data."""
        buffer_key = f"{chart_id}_{user_id}"
        if buffer_key in self._data_buffers:
            self._data_buffers[buffer_key] = []
    
    def get_stream_stats(self) -> Dict[str, Any]:
        """Get statistics about active streams."""
        return {
            "active_streams": len(self._active_streams),
            "streams": list(self._active_streams.keys()),
            "buffered_charts": len(self._data_buffers),
            "total_buffered_points": sum(len(b) for b in self._data_buffers.values()),
        }