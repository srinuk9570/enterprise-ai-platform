"""
Infrastructure Layer - Implementation Details (Adapters)
Contains concrete implementations of repositories, external service clients,
and framework-specific code.
"""
from src.infrastructure.database import DatabaseConnection, db_connection
from src.infrastructure.repositories import (
    SQLiteUserRepository,
    SQLiteConversationRepository,
    FileAssetRepository,
    ChromaMemoryRepository,
)
from src.infrastructure.llm import OllamaClient, ModelRegistry, StreamingHandler
from src.infrastructure.charting import MatplotlibEngine
from src.infrastructure.cache import MemoryCache
from src.infrastructure.logging import LoggerFactory, MetricsCollector
from src.infrastructure.security import JWTHandler, PasswordHasher, RateLimiter

__all__ = [
    # Database
    "DatabaseConnection",
    "db_connection",
    # Repositories
    "SQLiteUserRepository",
    "SQLiteConversationRepository",
    "FileAssetRepository",
    "ChromaMemoryRepository",
    # LLM
    "OllamaClient",
    "ModelRegistry",
    "StreamingHandler",
    # Charting
    "MatplotlibEngine",
    # Cache
    "MemoryCache",
    # Logging
    "LoggerFactory",
    "MetricsCollector",
    # Security
    "JWTHandler",
    "PasswordHasher",
    "RateLimiter",
]