"""
Repository Interfaces (Abstract) - Ports for data access.
"""
from src.domain.repositories.base_repository import BaseRepository
from src.domain.repositories.user_repository import IUserRepository
from src.domain.repositories.conversation_repository import IConversationRepository
from src.domain.repositories.asset_repository import IAssetRepository

__all__ = [
    "BaseRepository",
    "IUserRepository",
    "IConversationRepository",
    "IAssetRepository",
]