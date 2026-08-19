"""
Base WebSocket handler with common functionality.
"""
import logging
import json
from typing import Optional, Dict, Any, Callable
from uuid import UUID
import asyncio
from fastapi import WebSocket, WebSocketDisconnect

from src.presentation.websocket.connection_manager import ConnectionManager
from src.presentation.websocket.events.event_types import EventType, WebSocketEvent

logger = logging.getLogger(__name__)


class BaseWebSocketHandler:
    """
    Base handler for WebSocket connections with common patterns.
    """
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        self.manager = connection_manager or ConnectionManager()
        self._handlers: Dict[EventType, Callable] = {}
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        """Setup default message handlers. Override in subclass."""
        self._handlers = {
            EventType.PING: self._handle_ping,
        }
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        room: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Main connection handler loop.
        """
        room = room or f"user:{user_id}"
        
        await self.manager.connect(websocket, user_id, room, metadata)
        
        # Send welcome message
        await self._send_welcome(websocket, user_id, room)
        
        # Notify room of new user
        await self.manager.broadcast_json(
            WebSocketEvent(
                type=EventType.USER_JOINED,
                data={"user_id": user_id},
                room=room,
            ).to_dict(),
            room=room,
            exclude=websocket,
        )
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    await self._send_error(websocket, "Invalid JSON format")
                    continue
                
                # Process message
                await self._process_message(websocket, user_id, room, message_data)
                
        except WebSocketDisconnect:
            await self._handle_disconnect(websocket, user_id, room)
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
            await self._handle_disconnect(websocket, user_id, room)
    
    async def _process_message(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        message_data: Dict[str, Any],
    ) -> None:
        """
        Process an incoming message.
        """
        msg_type = message_data.get("type")
        
        if not msg_type:
            await self._send_error(websocket, "Missing 'type' field")
            return
        
        try:
            event_type = EventType(msg_type)
        except ValueError:
            await self._send_error(websocket, f"Unknown event type: {msg_type}")
            return
        
        # Find handler
        handler = self._handlers.get(event_type)
        
        if handler:
            await handler(websocket, user_id, room, message_data)
        else:
            await self._handle_unknown_message(websocket, user_id, room, message_data)
    
    async def _handle_ping(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle ping message."""
        await websocket.send_json({
            "type": EventType.PONG.value,
            "timestamp": data.get("timestamp"),
        })
    
    async def _handle_unknown_message(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle unknown message types. Override in subclass."""
        logger.debug(f"Unknown message type from {user_id}: {data.get('type')}")
    
    async def _send_welcome(self, websocket: WebSocket, user_id: str, room: str) -> None:
        """Send welcome message to new connection."""
        await websocket.send_json(
            WebSocketEvent(
                type=EventType.CONNECT,
                data={
                    "message": "Connected successfully",
                    "user_id": user_id,
                    "room": room,
                },
            ).to_dict()
        )
    
    async def _send_error(self, websocket: WebSocket, message: str, code: Optional[str] = None) -> None:
        """Send error message."""
        await websocket.send_json(
            WebSocketEvent.error(message, code).to_dict()
        )
    
    async def _handle_disconnect(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
    ) -> None:
        """Handle client disconnect."""
        await self.manager.disconnect(websocket)
        
        # Notify room of user leaving
        await self.manager.broadcast_json(
            WebSocketEvent(
                type=EventType.USER_LEFT,
                data={"user_id": user_id},
                room=room,
            ).to_dict(),
            room=room,
        )
    
    def register_handler(self, event_type: EventType, handler: Callable) -> None:
        """Register a custom message handler."""
        self._handlers[event_type] = handler
    
    def unregister_handler(self, event_type: EventType) -> None:
        """Unregister a message handler."""
        if event_type in self._handlers:
            del self._handlers[event_type]