"""
WebSocket client for real-time communication.
"""
import asyncio
import json
import logging
import threading
import time
import uuid
from typing import Optional, Dict, Any, Callable, List, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import websocket

import streamlit as st

logger = logging.getLogger(__name__)


class WebSocketState(Enum):
    """WebSocket connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class WebSocketEvent:
    """WebSocket event data."""
    
    type: str
    data: Optional[Dict[str, Any]] = None
    room: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketEvent":
        """Create event from dictionary."""
        return cls(
            type=data.get("type", "unknown"),
            data=data.get("data"),
            room=data.get("room"),
            user_id=data.get("user_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            event_id=data.get("event_id"),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "data": self.data,
            "room": self.room,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id,
        }


class WebSocketClient:
    """
    WebSocket client for real-time communication with the backend.
    Supports auto-reconnection, event handlers, and room management.
    """
    
    def __init__(
        self,
        base_url: str = "ws://localhost:8000",
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_delay: float = 1.0,
        ping_interval: int = 30,
        ping_timeout: int = 10,
    ):
        self.base_url = base_url
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        self._ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._state = WebSocketState.DISCONNECTED
        self._reconnect_count = 0
        self._should_run = False
        
        # Event handlers
        self._handlers: Dict[str, List[Callable]] = {}
        self._once_handlers: Dict[str, List[Callable]] = {}
        
        # Message queue for thread-safe communication
        self._message_queue: List[Dict[str, Any]] = []
        self._queue_lock = threading.Lock()
        
        # Connection metadata
        self._user_id: Optional[str] = None
        self._token: Optional[str] = None
        self._current_room: Optional[str] = None
        self._session_id: str = str(uuid.uuid4())
        
        # Streamlit session state integration
        self._use_session_state = True
    
    # ==================== Connection Management ====================
    
    def connect(
        self,
        user_id: Optional[str] = None,
        token: Optional[str] = None,
        endpoint: str = "/ws",
    ) -> bool:
        """
        Connect to WebSocket server.
        
        Args:
            user_id: User ID for authentication
            token: JWT token for authentication
            endpoint: WebSocket endpoint path
        
        Returns:
            True if connection initiated successfully
        """
        self._user_id = user_id or st.session_state.get("user", {}).get("id")
        self._token = token or st.session_state.get("token")
        
        # Build URL with auth
        url = f"{self.base_url}{endpoint}"
        if self._token:
            url += f"?token={self._token}"
        
        self._should_run = True
        self._state = WebSocketState.CONNECTING
        
        # Start WebSocket in background thread
        self._thread = threading.Thread(target=self._run_websocket, args=(url,))
        self._thread.daemon = True
        self._thread.start()
        
        return True
    
    def disconnect(self):
        """Disconnect from WebSocket server."""
        self._should_run = False
        self.auto_reconnect = False
        
        if self._ws:
            self._ws.close()
        
        self._state = WebSocketState.DISCONNECTED
        logger.info("WebSocket disconnected")
    
    def reconnect(self) -> bool:
        """Manually trigger reconnection."""
        if self._state == WebSocketState.CONNECTED:
            self.disconnect()
        
        self._reconnect_count = 0
        self.auto_reconnect = True
        
        return self.connect(self._user_id, self._token)
    
    # ==================== Event Handlers ====================
    
    def on(self, event_type: str, handler: Callable[[WebSocketEvent], None]):
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function that receives WebSocketEvent
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def once(self, event_type: str, handler: Callable[[WebSocketEvent], None]):
        """
        Register a one-time event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Callback function that receives WebSocketEvent
        """
        if event_type not in self._once_handlers:
            self._once_handlers[event_type] = []
        self._once_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Optional[Callable] = None):
        """
        Remove event handler(s).
        
        Args:
            event_type: Type of event
            handler: Specific handler to remove, or None to remove all
        """
        if handler is None:
            self._handlers.pop(event_type, None)
            self._once_handlers.pop(event_type, None)
        else:
            if event_type in self._handlers:
                self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]
            if event_type in self._once_handlers:
                self._once_handlers[event_type] = [h for h in self._once_handlers[event_type] if h != handler]
    
    def _trigger_handlers(self, event: WebSocketEvent):
        """Trigger registered handlers for an event."""
        # Regular handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in handler for {event.type}: {e}")
        
        # One-time handlers
        if event.type in self._once_handlers:
            handlers = self._once_handlers.pop(event.type)
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in once handler for {event.type}: {e}")
        
        # Wildcard handler
        if "*" in self._handlers:
            for handler in self._handlers["*"]:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error in wildcard handler: {e}")
    
    # ==================== Message Sending ====================
    
    def send(self, data: Dict[str, Any]) -> bool:
        """
        Send a message to the server.
        
        Args:
            data: Message data to send
        
        Returns:
            True if message queued successfully
        """
        if self._state != WebSocketState.CONNECTED:
            logger.warning("Cannot send message: WebSocket not connected")
            return False
        
        with self._queue_lock:
            self._message_queue.append(data)
        
        return True
    
    def send_event(self, event: WebSocketEvent) -> bool:
        """Send a WebSocketEvent."""
        return self.send(event.to_dict())
    
    def send_chat_message(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """Send a chat message."""
        return self.send({
            "type": "chat_message",
            "message": message,
            "conversation_id": conversation_id,
            "model": model,
            **kwargs,
        })
    
    def send_typing_indicator(self, conversation_id: str, is_typing: bool = True) -> bool:
        """Send typing indicator."""
        return self.send({
            "type": "typing",
            "conversation_id": conversation_id,
            "is_typing": is_typing,
        })
    
    def join_room(self, room: str) -> bool:
        """Join a room."""
        self._current_room = room
        return self.send({
            "type": "join_room",
            "room": room,
        })
    
    def leave_room(self, room: str) -> bool:
        """Leave a room."""
        if self._current_room == room:
            self._current_room = None
        return self.send({
            "type": "leave_room",
            "room": room,
        })
    
    # ==================== Internal Methods ====================
    
    def _run_websocket(self, url: str):
        """Run WebSocket connection in background thread."""
        self._ws = websocket.WebSocketApp(
            url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_ping=self._on_ping,
            on_pong=self._on_pong,
        )
        
        # Run with ping/pong
        self._ws.run_forever(
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
        )
    
    def _on_open(self, ws):
        """Called when WebSocket connection opens."""
        self._state = WebSocketState.CONNECTED
        self._reconnect_count = 0
        
        logger.info(f"WebSocket connected: {self._session_id}")
        
        # Send any queued messages
        self._flush_queue()
        
        # Trigger connect event
        self._trigger_handlers(WebSocketEvent(
            type="connect",
            data={"session_id": self._session_id},
        ))
    
    def _on_message(self, ws, message: str):
        """Called when a message is received."""
        try:
            data = json.loads(message)
            event = WebSocketEvent.from_dict(data)
            
            # Update session state if enabled
            if self._use_session_state:
                self._update_session_state(event)
            
            # Trigger handlers
            self._trigger_handlers(event)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse message: {message[:100]}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _on_error(self, ws, error):
        """Called when an error occurs."""
        self._state = WebSocketState.ERROR
        
        logger.error(f"WebSocket error: {error}")
        
        self._trigger_handlers(WebSocketEvent(
            type="error",
            data={"message": str(error)},
        ))
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closes."""
        self._state = WebSocketState.DISCONNECTED
        
        logger.info(f"WebSocket closed: {close_status_code} - {close_msg}")
        
        self._trigger_handlers(WebSocketEvent(
            type="disconnect",
            data={
                "code": close_status_code,
                "message": close_msg,
            },
        ))
        
        # Auto reconnect
        if self._should_run and self.auto_reconnect:
            self._attempt_reconnect()
    
    def _on_ping(self, ws, message):
        """Called when ping is received."""
        logger.debug("WebSocket ping received")
    
    def _on_pong(self, ws, message):
        """Called when pong is received."""
        logger.debug("WebSocket pong received")
    
    def _attempt_reconnect(self):
        """Attempt to reconnect with exponential backoff."""
        if self._reconnect_count >= self.max_reconnect_attempts:
            logger.error(f"Max reconnect attempts ({self.max_reconnect_attempts}) reached")
            self._state = WebSocketState.ERROR
            return
        
        self._state = WebSocketState.RECONNECTING
        self._reconnect_count += 1
        
        delay = self.reconnect_delay * (2 ** (self._reconnect_count - 1))
        
        logger.info(f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_count}/{self.max_reconnect_attempts})")
        
        self._trigger_handlers(WebSocketEvent(
            type="reconnecting",
            data={
                "attempt": self._reconnect_count,
                "max_attempts": self.max_reconnect_attempts,
                "delay": delay,
            },
        ))
        
        time.sleep(delay)
        
        if self._should_run:
            self.connect(self._user_id, self._token)
    
    def _flush_queue(self):
        """Send all queued messages."""
        with self._queue_lock:
            messages = self._message_queue.copy()
            self._message_queue.clear()
        
        for msg in messages:
            try:
                self._ws.send(json.dumps(msg))
            except Exception as e:
                logger.error(f"Failed to send queued message: {e}")
                with self._queue_lock:
                    self._message_queue.append(msg)
    
    def _update_session_state(self, event: WebSocketEvent):
        """Update Streamlit session state with event data."""
        try:
            if event.type == "chat_chunk":
                # Accumulate streaming response
                if "stream_content" not in st.session_state:
                    st.session_state["stream_content"] = ""
                st.session_state["stream_content"] += event.data.get("content", "")
            
            elif event.type == "chat_done":
                # Clear streaming state
                st.session_state.pop("stream_content", None)
            
            elif event.type == "conversation_created":
                st.session_state["current_conversation_id"] = event.data.get("conversation_id")
            
            elif event.type == "chart_update":
                # Update chart data
                if "chart_data" not in st.session_state:
                    st.session_state["chart_data"] = []
                st.session_state["chart_data"].append(event.data)
                
                # Keep buffer size reasonable
                if len(st.session_state["chart_data"]) > 500:
                    st.session_state["chart_data"] = st.session_state["chart_data"][-500:]
            
            elif event.type == "notification":
                # Add to notifications
                if "notifications" not in st.session_state:
                    st.session_state["notifications"] = []
                st.session_state["notifications"].append(event.data)
            
        except Exception as e:
            logger.error(f"Error updating session state: {e}")
    
    # ==================== Properties ====================
    
    @property
    def state(self) -> WebSocketState:
        """Get current connection state."""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._state == WebSocketState.CONNECTED
    
    @property
    def session_id(self) -> str:
        """Get session ID."""
        return self._session_id
    
    @property
    def current_room(self) -> Optional[str]:
        """Get current room."""
        return self._current_room


class ChatWebSocketClient(WebSocketClient):
    """
    Specialized WebSocket client for chat functionality.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stream_callbacks: Dict[str, Callable] = {}
        self._accumulated_content: Dict[str, str] = {}
    
    def connect_chat(self, conversation_id: Optional[str] = None) -> bool:
        """Connect to chat WebSocket."""
        endpoint = f"/ws/chat"
        if conversation_id:
            endpoint += f"?conversation_id={conversation_id}"
        
        connected = self.connect(endpoint=endpoint)
        
        if connected and conversation_id:
            self.join_room(f"chat:{conversation_id}")
        
        return connected
    
    def stream_message(
        self,
        message: str,
        on_chunk: Optional[Callable[[str], None]] = None,
        on_complete: Optional[Callable[[str], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> bool:
        """
        Stream a chat message with callbacks.
        
        Args:
            message: Message content
            on_chunk: Called for each token chunk
            on_complete: Called when stream completes
            on_error: Called on error
            **kwargs: Additional parameters
        
        Returns:
            True if message sent
        """
        stream_id = str(uuid.uuid4())
        self._accumulated_content[stream_id] = ""
        
        if on_chunk:
            self._stream_callbacks[f"{stream_id}_chunk"] = on_chunk
        if on_complete:
            self._stream_callbacks[f"{stream_id}_complete"] = on_complete
        if on_error:
            self._stream_callbacks[f"{stream_id}_error"] = on_error
        
        # Register handlers for this stream
        def handle_chunk(event: WebSocketEvent):
            content = event.data.get("content", "")
            self._accumulated_content[stream_id] += content
            
            callback = self._stream_callbacks.get(f"{stream_id}_chunk")
            if callback:
                callback(content)
        
        def handle_done(event: WebSocketEvent):
            accumulated = self._accumulated_content.pop(stream_id, "")
            
            callback = self._stream_callbacks.get(f"{stream_id}_complete")
            if callback:
                callback(accumulated)
            
            # Cleanup
            self.off(f"chat_chunk_{stream_id}")
            self.off(f"chat_done_{stream_id}")
            self.off(f"chat_error_{stream_id}")
            self._stream_callbacks.pop(f"{stream_id}_chunk", None)
            self._stream_callbacks.pop(f"{stream_id}_complete", None)
            self._stream_callbacks.pop(f"{stream_id}_error", None)
        
        def handle_error(event: WebSocketEvent):
            callback = self._stream_callbacks.get(f"{stream_id}_error")
            if callback:
                callback(event.data.get("message", "Unknown error"))
            
            # Cleanup
            self.off(f"chat_chunk_{stream_id}")
            self.off(f"chat_done_{stream_id}")
            self.off(f"chat_error_{stream_id}")
        
        self.on(f"chat_chunk_{stream_id}", handle_chunk)
        self.on(f"chat_done_{stream_id}", handle_done)
        self.on(f"chat_error_{stream_id}", handle_error)
        
        return self.send_chat_message(
            message=message,
            stream_id=stream_id,
            **kwargs,
        )
    
    def cancel_stream(self, stream_id: str):
        """Cancel an active stream."""
        self.send({
            "type": "stream_stop",
            "stream_id": stream_id,
        })
        
        # Cleanup
        self._accumulated_content.pop(stream_id, None)
        for key in list(self._stream_callbacks.keys()):
            if key.startswith(stream_id):
                self._stream_callbacks.pop(key, None)


class ChartWebSocketClient(WebSocketClient):
    """
    Specialized WebSocket client for real-time chart data.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._chart_buffers: Dict[str, List[Dict[str, Any]]] = {}
        self._stream_tasks: Dict[str, bool] = {}
    
    def connect_chart(self, chart_id: Optional[str] = None) -> bool:
        """Connect to chart WebSocket."""
        endpoint = f"/ws/chart"
        if chart_id:
            endpoint += f"?chart_id={chart_id}"
        
        connected = self.connect(endpoint=endpoint)
        
        if connected and chart_id:
            self.join_room(f"chart:{chart_id}")
        
        return connected
    
    def start_streaming(
        self,
        chart_id: str,
        data_source: str = "random",
        interval_ms: int = 1000,
        on_data: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs,
    ) -> bool:
        """
        Start streaming chart data.
        
        Args:
            chart_id: Chart identifier
            data_source: Type of data source
            interval_ms: Update interval in milliseconds
            on_data: Callback for each data point
            **kwargs: Additional chart configuration
        
        Returns:
            True if stream started
        """
        self._chart_buffers[chart_id] = []
        self._stream_tasks[chart_id] = True
        
        if on_data:
            def handle_data(event: WebSocketEvent):
                point = event.data.get("point", {})
                self._chart_buffers[chart_id].append(point)
                
                # Keep buffer size reasonable
                if len(self._chart_buffers[chart_id]) > 1000:
                    self._chart_buffers[chart_id] = self._chart_buffers[chart_id][-500:]
                
                on_data(point)
            
            self.on(f"chart_update_{chart_id}", handle_data)
        
        return self.send({
            "type": "stream_start",
            "chart_id": chart_id,
            "data_source": data_source,
            "interval_ms": interval_ms,
            **kwargs,
        })
    
    def stop_streaming(self, chart_id: str) -> bool:
        """Stop streaming chart data."""
        self._stream_tasks[chart_id] = False
        self.off(f"chart_update_{chart_id}")
        
        return self.send({
            "type": "stream_stop",
            "chart_id": chart_id,
        })
    
    def get_buffer(self, chart_id: str) -> List[Dict[str, Any]]:
        """Get buffered data for a chart."""
        return self._chart_buffers.get(chart_id, [])
    
    def clear_buffer(self, chart_id: str):
        """Clear buffered data."""
        if chart_id in self._chart_buffers:
            self._chart_buffers[chart_id] = []


# ==================== Singleton Client ====================

_ws_client: Optional[WebSocketClient] = None
_chat_ws_client: Optional[ChatWebSocketClient] = None
_chart_ws_client: Optional[ChartWebSocketClient] = None


def get_websocket_client() -> WebSocketClient:
    """Get or create global WebSocket client."""
    global _ws_client
    if _ws_client is None:
        _ws_client = WebSocketClient()
    return _ws_client


def get_chat_websocket_client() -> ChatWebSocketClient:
    """Get or create chat WebSocket client."""
    global _chat_ws_client
    if _chat_ws_client is None:
        _chat_ws_client = ChatWebSocketClient()
    return _chat_ws_client


def get_chart_websocket_client() -> ChartWebSocketClient:
    """Get or create chart WebSocket client."""
    global _chart_ws_client
    if _chart_ws_client is None:
        _chart_ws_client = ChartWebSocketClient()
    return _chart_ws_client


def disconnect_all():
    """Disconnect all WebSocket clients."""
    global _ws_client, _chat_ws_client, _chart_ws_client
    
    if _ws_client:
        _ws_client.disconnect()
        _ws_client = None
    
    if _chat_ws_client:
        _chat_ws_client.disconnect()
        _chat_ws_client = None
    
    if _chart_ws_client:
        _chart_ws_client.disconnect()
        _chart_ws_client = None