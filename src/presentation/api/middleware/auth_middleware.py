"""
Authentication middleware for FastAPI.
"""
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import HTTPException, status

from src.infrastructure.security import JWTHandler, ApiKeyManager

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT and API key authentication.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.jwt_handler = JWTHandler()
        self.api_key_manager = ApiKeyManager()
        self.exclude_paths = exclude_paths or [
            "/api/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")
        
        user = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            is_valid, payload, _ = self.jwt_handler.validate_access_token(token)
            
            if is_valid:
                user = {
                    "id": payload["sub"],
                    "username": payload.get("username"),
                    "role": payload.get("role"),
                }
        
        elif api_key:
            # Validate API key
            is_valid, user_id, scopes, _ = await self.api_key_manager.validate_api_key(api_key)
            
            if is_valid:
                user = {
                    "id": str(user_id),
                    "auth_type": "api_key",
                    "scopes": scopes,
                }
        
        # Attach user to request state
        request.state.user = user
        
        return await call_next(request)