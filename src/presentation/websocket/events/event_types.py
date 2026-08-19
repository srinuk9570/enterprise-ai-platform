"""
WebSocket event type definitions.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime
import json


class EventType(str, Enum):
    """WebSocket event types."""
    
    # Connection events
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    
    # Chat events
    CHAT_MESSAGE = "chat_message"
    CHAT_CHUNK = "chat_chunk"
    CHAT_DONE = "chat_done"
    CHAT_ERROR = "chat_error"
    TYPING = "typing"
    MESSAGE_RECEIVED = "message_received"
    
    # Conversation events
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_UPDATED = "conversation_updated"
    CONVERSATION_DELETED = "conversation_deleted"
    CONVERSATION_JOINED = "conversation_joined"
    CONVERSATION_LEFT = "conversation_left"
    
    # Chart events
    CHART_DATA = "chart_data"
    CHART_UPDATE = "chart_update"
    CHART_GENERATED = "chart_generated"
    CHART_ERROR = "chart_error"
    STREAM_START = "stream_start"
    STREAM_STOP = "stream_stop"
    
    # Image events
    IMAGE_GENERATED = "image_generated"
    IMAGE_PROGRESS = "image_progress"
    IMAGE_ERROR = "image_error"
    
    # User events
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_UPDATED = "user_updated"
    
    # System events
    NOTIFICATION = "notification"
    RATE_LIMIT = "rate_limit"
    MODEL_STATUS = "model_status"


@dataclass
class WebSocketEvent:
    """
    WebSocket event data structure.
    """
    
    type: EventType
    data: Optional[Dict[str, Any]] = None
    room: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        result = {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.data:
            result["data"] = self.data
        if self.room:
            result["room"] = self.room
        if self.user_id:
            result["user_id"] = self.user_id
        if self.event_id:
            result["event_id"] = self.event_id
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WebSocketEvent":
        """Create event from dictionary."""
        return cls(
            type=EventType(data["type"]),
            data=data.get("data"),
            room=data.get("room"),
            user_id=data.get("user_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            event_id=data.get("event_id"),
            correlation_id=data.get("correlation_id"),
        )
    
    @classmethod
    def chat_message(cls, content: str, user_id: str, room: str) -> "WebSocketEvent":
        """Create a chat message event."""
        return cls(
            type=EventType.CHAT_MESSAGE,
            data={"content": content},
            user_id=user_id,
            room=room,
        )
    
    @classmethod
    def chat_chunk(cls, content: str, room: str) -> "WebSocketEvent":
        """Create a chat chunk event."""
        return cls(
            type=EventType.CHAT_CHUNK,
            data={"content": content},
            room=room,
        )
    
    @classmethod
    def error(cls, message: str, code: Optional[str] = None) -> "WebSocketEvent":
        """Create an error event."""
        return cls(
            type=EventType.ERROR,
            data={"message": message, "code": code},
        )
    
    @classmethod
    def notification(cls, message: str, level: str = "info") -> "WebSocketEvent":
        """Create a notification event."""
        return cls(
            type=EventType.NOTIFICATION,
            data={"message": message, "level": level},
        )
    
    @classmethod
    def chart_update(cls, chart_data: Dict[str, Any], room: str) -> "WebSocketEvent":
        """Create a chart update event."""
        return cls(
            type=EventType.CHART_UPDATE,
            data=chart_data,
            room=room,
        )