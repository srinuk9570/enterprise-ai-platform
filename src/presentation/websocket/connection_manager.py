"""
WebSocket connection manager for handling multiple connections.
"""
import logging
import asyncio
from typing import Dict, Set, Any, Optional, List
from uuid import UUID
import json
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections with room-based broadcasting.
    """
    
    def __init__(self):
        # Room -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        
        # User ID -> WebSocket connection
        self.user_connections: Dict[str, WebSocket] = {}
        
        # WebSocket -> User ID (reverse mapping)
        self.ws_to_user: Dict[WebSocket, str] = {}
        
        # WebSocket -> Rooms (for cleanup)
        self.ws_to_rooms: Dict[WebSocket, Set[str]] = {}
        
        # Connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        room: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Accept a WebSocket connection and add to room.
        """
        await websocket.accept()
        
        async with self._lock:
            # Create room if not exists
            if room not in self.active_connections:
                self.active_connections[room] = set()
            
            # Add to room
            self.active_connections[room].add(websocket)
            
            # Track user connection
            self.user_connections[user_id] = websocket
            self.ws_to_user[websocket] = user_id
            
            # Track rooms for this connection
            if websocket not in self.ws_to_rooms:
                self.ws_to_rooms[websocket] = set()
            self.ws_to_rooms[websocket].add(room)
            
            # Store metadata
            if metadata:
                self.connection_metadata[websocket] = {
                    **metadata,
                    "connected_at": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                }
            else:
                self.connection_metadata[websocket] = {
                    "connected_at": datetime.utcnow().isoformat(),
                    "user_id": user_id,
                }
        
        logger.info(f"WebSocket connected: user={user_id}, room={room}, total_connections={self.get_total_connections()}")
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from all rooms.
        """
        async with self._lock:
            user_id = self.ws_to_user.get(websocket)
            
            # Remove from all rooms
            if websocket in self.ws_to_rooms:
                for room in self.ws_to_rooms[websocket]:
                    if room in self.active_connections:
                        self.active_connections[room].discard(websocket)
                        # Clean up empty rooms
                        if not self.active_connections[room]:
                            del self.active_connections[room]
                
                del self.ws_to_rooms[websocket]
            
            # Remove user mapping
            if user_id and user_id in self.user_connections:
                del self.user_connections[user_id]
            
            # Remove reverse mapping
            if websocket in self.ws_to_user:
                del self.ws_to_user[websocket]
            
            # Remove metadata
            if websocket in self.connection_metadata:
                del self.connection_metadata[websocket]
        
        if user_id:
            logger.info(f"WebSocket disconnected: user={user_id}, remaining_connections={self.get_total_connections()}")
    
    async def send_personal_message(self, message: Any, user_id: str) -> bool:
        """
        Send a message to a specific user.
        Returns True if successful, False otherwise.
        """
        if user_id not in self.user_connections:
            logger.warning(f"User {user_id} not connected")
            return False
        
        websocket = self.user_connections[user_id]
        
        try:
            if isinstance(message, dict):
                message = json.dumps(message, default=str)
            await websocket.send_text(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            await self.disconnect(websocket)
            return False
    
    async def send_personal_json(self, data: Dict[str, Any], user_id: str) -> bool:
        """
        Send JSON data to a specific user.
        """
        return await self.send_personal_message(data, user_id)
    
    async def broadcast(
        self,
        message: Any,
        room: str = "default",
        exclude: Optional[WebSocket] = None,
    ) -> int:
        """
        Broadcast a message to all connections in a room.
        Returns number of successful sends.
        """
        if room not in self.active_connections:
            return 0
        
        if isinstance(message, dict):
            message = json.dumps(message, default=str)
        
        sent_count = 0
        disconnected = set()
        
        for websocket in self.active_connections[room]:
            if websocket == exclude:
                continue
            
            try:
                await websocket.send_text(message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to websocket: {e}")
                disconnected.add(websocket)
        
        # Clean up disconnected
        for ws in disconnected:
            await self.disconnect(ws)
        
        return sent_count
    
    async def broadcast_json(
        self,
        data: Dict[str, Any],
        room: str = "default",
        exclude: Optional[WebSocket] = None,
    ) -> int:
        """
        Broadcast JSON data to a room.
        """
        return await self.broadcast(data, room, exclude)
    
    async def broadcast_to_multiple(
        self,
        message: Any,
        rooms: List[str],
        exclude: Optional[WebSocket] = None,
    ) -> int:
        """
        Broadcast to multiple rooms.
        """
        total_sent = 0
        for room in rooms:
            total_sent += await self.broadcast(message, room, exclude)
        return total_sent
    
    async def send_to_users(
        self,
        message: Any,
        user_ids: List[str],
    ) -> int:
        """
        Send a message to multiple specific users.
        """
        sent_count = 0
        for user_id in user_ids:
            if await self.send_personal_message(message, user_id):
                sent_count += 1
        return sent_count
    
    def get_room_count(self, room: str = "default") -> int:
        """Get number of connections in a room."""
        return len(self.active_connections.get(room, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return len(self.ws_to_user)
    
    def get_room_members(self, room: str = "default") -> List[str]:
        """Get list of user IDs in a room."""
        if room not in self.active_connections:
            return []
        
        members = []
        for ws in self.active_connections[room]:
            user_id = self.ws_to_user.get(ws)
            if user_id:
                members.append(user_id)
        return members
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user is connected."""
        return user_id in self.user_connections
    
    def get_user_rooms(self, user_id: str) -> List[str]:
        """Get all rooms a user is connected to."""
        if user_id not in self.user_connections:
            return []
        
        websocket = self.user_connections[user_id]
        return list(self.ws_to_rooms.get(websocket, set()))
    
    async def move_connection(
        self,
        websocket: WebSocket,
        from_room: str,
        to_room: str,
    ) -> None:
        """
        Move a connection from one room to another.
        """
        async with self._lock:
            # Remove from old room
            if from_room in self.active_connections:
                self.active_connections[from_room].discard(websocket)
                if not self.active_connections[from_room]:
                    del self.active_connections[from_room]
            
            # Add to new room
            if to_room not in self.active_connections:
                self.active_connections[to_room] = set()
            self.active_connections[to_room].add(websocket)
            
            # Update room tracking
            if websocket in self.ws_to_rooms:
                self.ws_to_rooms[websocket].discard(from_room)
                self.ws_to_rooms[websocket].add(to_room)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": self.get_total_connections(),
            "total_rooms": len(self.active_connections),
            "rooms": {
                room: len(connections)
                for room, connections in self.active_connections.items()
            },
            "users_connected": len(self.user_connections),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def close_all_connections(self) -> int:
        """
        Close all active connections gracefully.
        Returns number of connections closed.
        """
        closed_count = 0
        
        for websocket in list(self.ws_to_user.keys()):
            try:
                await websocket.close(code=1000, reason="Server shutting down")
                closed_count += 1
            except Exception:
                pass
        
        # Clear all data
        async with self._lock:
            self.active_connections.clear()
            self.user_connections.clear()
            self.ws_to_user.clear()
            self.ws_to_rooms.clear()
            self.connection_metadata.clear()
        
        logger.info(f"Closed {closed_count} WebSocket connections")
        return closed_count
    
    async def heartbeat_check(self) -> int:
        """
        Check all connections and remove dead ones.
        Returns number of dead connections removed.
        """
        dead_connections = []
        
        for websocket in self.ws_to_user.keys():
            try:
                # Send ping
                await websocket.send_json({"type": "ping"})
            except Exception:
                dead_connections.append(websocket)
        
        for ws in dead_connections:
            await self.disconnect(ws)
        
        if dead_connections:
            logger.info(f"Removed {len(dead_connections)} dead connections")
        
        return len(dead_connections)