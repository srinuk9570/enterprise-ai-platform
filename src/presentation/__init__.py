"""
Presentation Layer - API, WebSocket, and Web UI.
"""

# Don't try to import APIRouter from our modules - it's from fastapi
# Remove or comment out this line:
# from src.presentation.api import APIRouter

# Instead, if you need to export routers:
from src.presentation.api import create_app

__all__ = [
    "create_app",
]