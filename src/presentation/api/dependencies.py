"""
FastAPI dependency injection container.
"""
from typing import Optional, Callable
from functools import lru_cache

from fastapi import Depends, Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.infrastructure.database.sqlite.connection import db_connection
from src.infrastructure.repositories import (
    SQLiteUserRepository,
    SQLiteConversationRepository,
    FileAssetRepository,
    ChromaMemoryRepository,
)
from src.infrastructure.llm import OllamaClient, ModelRegistry, StreamingHandler
from src.infrastructure.llm.prompt_templates import PromptTemplateManager
from src.infrastructure.charting import MatplotlibEngine
from src.infrastructure.cache import MemoryCache
from src.infrastructure.security import (
    JWTHandler,
    PasswordHasher,
    RateLimiter,
    ApiKeyManager,
    AuditLogger,
)
from src.infrastructure.logging import LoggerFactory
from src.infrastructure.database.vector_store.embedding_service import EmbeddingService
from src.infrastructure.database.vector_store.chroma_client import ChromaClient

from src.domain.services import (
    AuthenticationService,
    LLMOrchestrationService,
    ChartGenerationService,
)
from src.application.handlers import (
    UserCommandHandler,
    ConversationCommandHandler,
    AssetCommandHandler,
    ConversationQueryHandler,
    AnalyticsQueryHandler,
)


# Security
security = HTTPBearer(auto_error=False)


# Singleton instances with caching
@lru_cache()
def get_jwt_handler() -> JWTHandler:
    return JWTHandler()


@lru_cache()
def get_password_hasher() -> PasswordHasher:
    return PasswordHasher()


@lru_cache()
def get_rate_limiter() -> RateLimiter:
    return RateLimiter()


@lru_cache()
def get_api_key_manager() -> ApiKeyManager:
    return ApiKeyManager()


@lru_cache()
def get_audit_logger() -> AuditLogger:
    return AuditLogger()


@lru_cache()
def get_logger_factory() -> LoggerFactory:
    return LoggerFactory()


# Repositories
@lru_cache()
def get_user_repository() -> SQLiteUserRepository:
    return SQLiteUserRepository()


@lru_cache()
def get_conversation_repository() -> SQLiteConversationRepository:
    return SQLiteConversationRepository()


@lru_cache()
def get_asset_repository() -> FileAssetRepository:
    return FileAssetRepository()


def get_chroma_client() -> ChromaClient:
    return ChromaClient()


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_memory_repository() -> ChromaMemoryRepository:
    return ChromaMemoryRepository(
        chroma_client=get_chroma_client(),
        embedding_service=get_embedding_service(),
    )


# LLM Components
@lru_cache()
def get_ollama_client() -> OllamaClient:
    return OllamaClient()


@lru_cache()
def get_model_registry() -> ModelRegistry:
    return ModelRegistry(ollama_client=get_ollama_client())


@lru_cache()
def get_streaming_handler() -> StreamingHandler:
    return StreamingHandler(ollama_client=get_ollama_client())


@lru_cache()
def get_prompt_template_manager() -> PromptTemplateManager:
    return PromptTemplateManager()


# Chart Components
@lru_cache()
def get_chart_engine() -> MatplotlibEngine:
    return MatplotlibEngine()


# Cache
@lru_cache()
def get_cache() -> MemoryCache:
    return MemoryCache()


# Domain Services
def get_authentication_service() -> AuthenticationService:
    return AuthenticationService(
        user_repository=get_user_repository(),
        password_hasher=get_password_hasher(),
    )


def get_llm_service() -> LLMOrchestrationService:
    return LLMOrchestrationService(
        llm_client=get_ollama_client(),
        conversation_repository=get_conversation_repository(),
        message_repository=get_conversation_repository(),
        asset_repository=get_asset_repository(),
        rate_limiter=get_rate_limiter(),
    )


def get_chart_service() -> ChartGenerationService:
    return ChartGenerationService(
        asset_repository=get_asset_repository(),
        chart_config_repository=None,  # To be implemented
        data_source_provider=None,  # To be implemented
        chart_renderer=get_chart_engine(),
    )


# Application Handlers
def get_user_command_handler() -> UserCommandHandler:
    return UserCommandHandler(
        user_repository=get_user_repository(),
        authentication_service=get_authentication_service(),
    )


def get_conversation_command_handler() -> ConversationCommandHandler:
    return ConversationCommandHandler(
        conversation_repository=get_conversation_repository(),
        message_repository=get_conversation_repository(),
        llm_service=get_llm_service(),
        user_repository=get_user_repository(),
    )


def get_asset_command_handler() -> AssetCommandHandler:
    return AssetCommandHandler(
        asset_repository=get_asset_repository(),
        chart_config_repository=None,
        llm_service=get_llm_service(),
        chart_service=get_chart_service(),
        user_repository=get_user_repository(),
    )


def get_conversation_query_handler() -> ConversationQueryHandler:
    return ConversationQueryHandler(
        conversation_repository=get_conversation_repository(),
        message_repository=get_conversation_repository(),
        user_repository=get_user_repository(),
    )


def get_analytics_query_handler() -> AnalyticsQueryHandler:
    return AnalyticsQueryHandler(
        user_repository=get_user_repository(),
        conversation_repository=get_conversation_repository(),
        asset_repository=get_asset_repository(),
        chart_config_repository=None,
        chart_service=get_chart_service(),
    )


# Authentication dependency
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Get current authenticated user from JWT token or API key.
    """
    if not credentials:
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            api_key_manager = get_api_key_manager()
            is_valid, user_id, scopes, _ = await api_key_manager.validate_api_key(api_key)
            if is_valid:
                user_repo = get_user_repository()
                from uuid import UUID
                user = await user_repo.get_by_id(UUID(user_id)) if user_id else None
                if user:
                    return {
                        "user_id": str(user.id),
                        "username": user.username,
                        "role": user.role.value,
                        "auth_type": "api_key",
                        "scopes": scopes,
                    }
        return None
    
    token = credentials.credentials
    jwt_handler = get_jwt_handler()
    
    is_valid, payload, _ = jwt_handler.validate_access_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "user_id": payload["sub"],
        "username": payload.get("username"),
        "role": payload.get("role"),
        "email": payload.get("email"),
        "auth_type": "jwt",
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Get current active user (raises 401 if not authenticated).
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def get_admin_user(
    current_user: dict = Depends(get_current_active_user),
) -> dict:
    """
    Get current user with admin role (raises 403 if not admin).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


class Dependencies:
    """
    Container for all dependencies.
    """
    
    def __init__(self):
        self.jwt_handler = get_jwt_handler()
        self.password_hasher = get_password_hasher()
        self.rate_limiter = get_rate_limiter()
        self.audit_logger = get_audit_logger()
        
        self.user_repository = get_user_repository()
        self.conversation_repository = get_conversation_repository()
        self.asset_repository = get_asset_repository()
        
        self.ollama_client = get_ollama_client()
        self.model_registry = get_model_registry()
        self.streaming_handler = get_streaming_handler()
        
        self.auth_service = get_authentication_service()
        self.llm_service = get_llm_service()
        self.chart_service = get_chart_service()
        
        self.user_command_handler = get_user_command_handler()
        self.conversation_command_handler = get_conversation_command_handler()
        self.asset_command_handler = get_asset_command_handler()
        self.conversation_query_handler = get_conversation_query_handler()
        self.analytics_query_handler = get_analytics_query_handler()


@lru_cache()
def get_dependencies() -> Dependencies:
    """Get cached dependencies container."""
    return Dependencies()