"""
REST API - FastAPI application and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.presentation.api.dependencies import get_dependencies
from src.presentation.api.middleware import (
    AuthMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
)
from src.presentation.api.routes import (
    auth_routes,
    conversation_routes,
    llm_routes,
    chart_routes,
    image_generation_routes,
    admin_routes,
)
from src.shared.config import settings


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Enterprise AI Platform - Local LLM, Charts, and Image Generation",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Include routers
    app.include_router(auth_routes.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(conversation_routes.router, prefix="/api/conversations", tags=["Conversations"])
    app.include_router(llm_routes.router, prefix="/api/llm", tags=["LLM"])
    app.include_router(chart_routes.router, prefix="/api/charts", tags=["Charts"])
    app.include_router(image_generation_routes.router, prefix="/api/images", tags=["Images"])
    app.include_router(admin_routes.router, prefix="/api/admin", tags=["Admin"])
    
    # Health check endpoint
    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "version": settings.APP_VERSION}
    
    return app


__all__ = [
    "create_app",
    "auth_routes",
    "conversation_routes",
    "llm_routes",
    "chart_routes",
    "image_generation_routes",
    "admin_routes",
]