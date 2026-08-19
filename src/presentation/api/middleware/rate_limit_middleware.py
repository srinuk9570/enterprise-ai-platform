"""
Rate limiting middleware for FastAPI.
"""
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import status

from src.infrastructure.security import RateLimiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.exclude_paths = exclude_paths or [
            "/api/health",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get identifier (user ID or IP)
        identifier = self._get_identifier(request)
        
        # Determine endpoint type for rate limit tier
        endpoint_type = self._get_endpoint_type(request.url.path)
        
        # Check rate limit
        allowed, wait_time = self.rate_limiter.check_sync(
            identifier=identifier,
            endpoint_type=endpoint_type,
        )
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {identifier} on {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {wait_time} seconds.",
                    "retry_after": wait_time,
                },
                headers={"Retry-After": str(wait_time)},
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining(identifier, endpoint_type)
        if remaining is not None:
            response.headers["X-RateLimit-Remaining"] = str(int(remaining))
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting."""
        # Try to get user ID from request state
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.get('id')}"
        
        # Fall back to IP address
        return f"ip:{request.client.host}" if request.client else "unknown"
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type from path."""
        if "/api/chat" in path or "/api/llm/chat" in path:
            return "chat"
        elif "/api/images/generate" in path:
            return "image_generation"
        elif "/api/auth" in path:
            return "auth"
        elif "/api/admin" in path:
            return "admin"
        else:
            return "default"