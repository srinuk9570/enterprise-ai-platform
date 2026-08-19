"""
FastAPI route modules.
"""
from src.presentation.api.routes import (
    auth_routes,
    conversation_routes,
    llm_routes,
    chart_routes,
    image_generation_routes,
    admin_routes,
)

__all__ = [
    "auth_routes",
    "conversation_routes",
    "llm_routes",
    "chart_routes",
    "image_generation_routes",
    "admin_routes",
]