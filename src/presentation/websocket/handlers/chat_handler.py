"""
WebSocket handler for real-time chat.
"""
import logging
import json
from typing import Optional, Dict, Any
from uuid import UUID
import asyncio
from fastapi import WebSocket

from src.presentation.websocket.handlers.base_handler import BaseWebSocketHandler
from src.presentation.websocket.connection_manager import ConnectionManager
from src.presentation.websocket.events.event_types import EventType, WebSocketEvent
from src.presentation.api.dependencies import get_dependencies

logger = logging.getLogger(__name__)


class ChatWebSocketHandler(BaseWebSocketHandler):
    """
    Handler for chat WebSocket connections with streaming support.
    """
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        super().__init__(connection_manager)
        self._active_streams: Dict[str, asyncio.Task] = {}
    
    def _setup_handlers(self) -> None:
        """Setup chat-specific handlers."""
        super()._setup_handlers()
        
        self._handlers.update({
            EventType.CHAT_MESSAGE: self._handle_chat_message,
            EventType.TYPING: self._handle_typing,
            EventType.CONVERSATION_JOINED: self._handle_join_conversation,
            EventType.CONVERSATION_LEFT: self._handle_leave_conversation,
            EventType.STREAM_START: self._handle_stream_start,
            EventType.STREAM_STOP: self._handle_stream_stop,
        })
    
    async def handle_connection(
        self,
        websocket: WebSocket,
        user_id: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Handle a chat WebSocket connection.
        """
        room = f"chat:{conversation_id}" if conversation_id else f"user:{user_id}"
        
        metadata = metadata or {}
        metadata["conversation_id"] = conversation_id
        
        await super().handle_connection(websocket, user_id, room, metadata)
    
    async def _handle_chat_message(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Handle incoming chat message.
        """
        message = data.get("message", "")
        temp_id = data.get("temp_id")
        conversation_id = data.get("conversation_id")
        model = data.get("model")
        system_prompt = data.get("system_prompt")
        stream = data.get("stream", True)
        
        if not message:
            await self._send_error(websocket, "Message cannot be empty")
            return
        
        # Send acknowledgment
        await self.manager.send_personal_json(
            WebSocketEvent(
                type=EventType.MESSAGE_RECEIVED,
                data={"temp_id": temp_id, "message": message[:50]},
            ).to_dict(),
            user_id,
        )
        
        deps = get_dependencies()
        
        # Create or get conversation
        conv_id = UUID(conversation_id) if conversation_id else None
        
        if not conv_id:
            # Create new conversation
            conv_dto, errors = await deps.conversation_command_handler.create_conversation(
                user_id=UUID(user_id),
                model_name=model or deps.ollama_client.default_model,
            )
            
            if errors:
                await self.manager.send_personal_json(
                    WebSocketEvent.error(errors[0], "CONVERSATION_CREATE_FAILED").to_dict(),
                    user_id,
                )
                return
            
            conv_id = UUID(conv_dto.id)
            
            # Notify client of new conversation
            await self.manager.send_personal_json(
                WebSocketEvent(
                    type=EventType.CONVERSATION_CREATED,
                    data={"conversation_id": str(conv_id), "title": conv_dto.title},
                ).to_dict(),
                user_id,
            )
            
            # Move to new room
            new_room = f"chat:{conv_id}"
            await self.manager.move_connection(websocket, room, new_room)
            room = new_room
        
        # Create chat command
        from src.application.commands import SendMessageCommand
        
        command = SendMessageCommand(
            conversation_id=conv_id,
            content=message,
            user_id=UUID(user_id),
            model_name=model,
            system_prompt=system_prompt,
            stream_response=stream,
            model_parameters=data.get("parameters"),
        )
        
        if stream:
            # Stream response
            await self._stream_response(command, conv_id, user_id, room, deps)
        else:
            # Non-streaming response
            response_dto, errors = await deps.conversation_command_handler.handle_send_message(command)
            
            if errors:
                await self.manager.send_personal_json(
                    WebSocketEvent.error(errors[0], "CHAT_ERROR").to_dict(),
                    user_id,
                )
                return
            
            # Send response
            await self.manager.broadcast_json(
                WebSocketEvent(
                    type=EventType.CHAT_DONE,
                    data={
                        "conversation_id": str(conv_id),
                        "message": response_dto.content,
                        "model_used": response_dto.model_used,
                        "tokens_used": response_dto.tokens_used,
                        "generation_time_ms": response_dto.generation_time_ms,
                    },
                ).to_dict(),
                room=room,
            )
    
    async def _stream_response(
        self,
        command,
        conv_id: UUID,
        user_id: str,
        room: str,
        deps,
    ) -> None:
        """
        Stream response chunks to the room.
        """
        stream_id = f"{conv_id}_{user_id}"
        
        async def stream_task():
            try:
                accumulated = ""
                
                async for chunk in deps.conversation_command_handler.handle_stream_message(command):
                    if isinstance(chunk, str):
                        accumulated += chunk
                        
                        # Send chunk to room
                        await self.manager.broadcast_json(
                            WebSocketEvent.chat_chunk(chunk, room).to_dict(),
                            room=room,
                        )
                
                # Send completion
                await self.manager.broadcast_json(
                    WebSocketEvent(
                        type=EventType.CHAT_DONE,
                        data={
                            "conversation_id": str(conv_id),
                            "accumulated": accumulated,
                        },
                    ).to_dict(),
                    room=room,
                )
                
            except asyncio.CancelledError:
                logger.info(f"Stream {stream_id} cancelled")
                await self.manager.broadcast_json(
                    WebSocketEvent(
                        type=EventType.STREAM_STOP,
                        data={"conversation_id": str(conv_id)},
                    ).to_dict(),
                    room=room,
                )
            except Exception as e:
                logger.error(f"Stream error: {e}")
                await self.manager.broadcast_json(
                    WebSocketEvent.error(str(e), "STREAM_ERROR").to_dict(),
                    room=room,
                )
            finally:
                self._active_streams.pop(stream_id, None)
        
        # Create and store task
        task = asyncio.create_task(stream_task())
        self._active_streams[stream_id] = task
    
    async def _handle_typing(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle typing indicator."""
        await self.manager.broadcast_json(
            WebSocketEvent(
                type=EventType.TYPING,
                data={"user_id": user_id},
            ).to_dict(),
            room=room,
            exclude=websocket,
        )
    
    async def _handle_join_conversation(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle joining a conversation."""
        conversation_id = data.get("conversation_id")
        
        if not conversation_id:
            await self._send_error(websocket, "Missing conversation_id")
            return
        
        new_room = f"chat:{conversation_id}"
        await self.manager.move_connection(websocket, room, new_room)
        
        await self.manager.send_personal_json(
            WebSocketEvent(
                type=EventType.CONVERSATION_JOINED,
                data={"conversation_id": conversation_id},
            ).to_dict(),
            user_id,
        )
    
    async def _handle_leave_conversation(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle leaving a conversation."""
        user_room = f"user:{user_id}"
        await self.manager.move_connection(websocket, room, user_room)
        
        await self.manager.send_personal_json(
            WebSocketEvent(
                type=EventType.CONVERSATION_LEFT,
                data={},
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
        """Handle stream start request."""
        # Already handled in chat message
        pass
    
    async def _handle_stream_stop(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str,
        data: Dict[str, Any],
    ) -> None:
        """Handle stream stop request."""
        conversation_id = data.get("conversation_id")
        
        if not conversation_id:
            await self._send_error(websocket, "Missing conversation_id")
            return
        
        stream_id = f"{conversation_id}_{user_id}"
        
        if stream_id in self._active_streams:
            self._active_streams[stream_id].cancel()
            await self.manager.send_personal_json(
                WebSocketEvent(
                    type=EventType.STREAM_STOP,
                    data={"conversation_id": conversation_id},
                ).to_dict(),
                user_id,
            )
    
    def cancel_stream(self, conversation_id: str, user_id: str) -> bool:
        """Cancel an active stream."""
        stream_id = f"{conversation_id}_{user_id}"
        
        if stream_id in self._active_streams:
            self._active_streams[stream_id].cancel()
            return True
        return False
    
    def get_active_streams(self) -> Dict[str, bool]:
        """Get status of active streams."""
        return {
            stream_id: not task.done()
            for stream_id, task in self._active_streams.items()
        }