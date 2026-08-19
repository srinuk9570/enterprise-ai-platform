"""
WebSocket route definitions for FastAPI.
"""
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from uuid import UUID

from src.presentation.websocket.connection_manager import ConnectionManager
from src.presentation.websocket.handlers.chat_handler import ChatWebSocketHandler
from src.presentation.websocket.handlers.chart_stream_handler import ChartStreamHandler
from src.presentation.api.dependencies import get_current_user_ws, get_dependencies

logger = logging.getLogger(__name__)

router = APIRouter()

# Global connection manager
connection_manager = ConnectionManager()
chat_handler = ChatWebSocketHandler(connection_manager)
chart_handler = ChartStreamHandler(connection_manager)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    Main WebSocket endpoint for general connections.
    """
    # Authenticate user
    user = await get_current_user_ws(token)
    
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = user["user_id"]
    
    await chat_handler.handle_connection(websocket, user_id)


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    conversation_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for chat with streaming responses.
    """
    user = await get_current_user_ws(token)
    
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = user["user_id"]
    
    await chat_handler.handle_connection(
        websocket,
        user_id,
        conversation_id=conversation_id,
    )


@router.websocket("/ws/chart")
async def chart_websocket(
    websocket: WebSocket,
    chart_id: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for real-time chart data streaming.
    """
    user = await get_current_user_ws(token)
    
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = user["user_id"]
    
    await chart_handler.handle_connection(
        websocket,
        user_id,
        chart_id=chart_id,
    )


@router.websocket("/ws/notifications")
async def notifications_websocket(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for system notifications.
    """
    user = await get_current_user_ws(token)
    
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return
    
    user_id = user["user_id"]
    room = f"notifications:{user_id}"
    
    await connection_manager.connect(websocket, user_id, room)
    
    try:
        # Send welcome
        await connection_manager.send_personal_json(
            {"type": "connected", "message": "Notification service connected"},
            user_id,
        )
        
        while True:
            # Keep connection alive, wait for messages
            data = await websocket.receive_text()
            
            # Echo back for now (can be extended)
            await connection_manager.send_personal_json(
                {"type": "echo", "data": data},
                user_id,
            )
            
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        logger.info(f"Notification WebSocket disconnected: {user_id}")


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    Get WebSocket connection statistics.
    """
    return {
        "connections": connection_manager.get_connection_stats(),
        "chat_streams": chat_handler.get_active_streams(),
        "chart_streams": chart_handler.get_stream_stats(),
    }


# Helper function for WebSocket authentication
async def get_current_user_ws(token: Optional[str]) -> Optional[dict]:
    """
    Authenticate WebSocket connection using token.
    """
    if not token:
        return None
    
    deps = get_dependencies()
    
    # Validate JWT token
    is_valid, payload, _ = deps.jwt_handler.validate_access_token(token)
    
    if not is_valid:
        # Try API key
        api_key_manager = deps.api_key_manager
        is_valid, user_id, scopes, _ = await api_key_manager.validate_api_key(token)
        
        if is_valid and user_id:
            return {
                "user_id": str(user_id),
                "auth_type": "api_key",
                "scopes": scopes,
            }
        
        return None
    
    return {
        "user_id": payload["sub"],
        "username": payload.get("username"),
        "role": payload.get("role"),
        "auth_type": "jwt",
    }