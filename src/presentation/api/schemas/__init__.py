"""
Pydantic schemas for API requests and responses.
"""
from src.presentation.api.schemas.request_schemas import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ChatRequest,
    ChatStreamRequest,
    CreateConversationRequest,
    UpdateConversationRequest,
)
from src.presentation.api.schemas.response_schemas import (
    TokenResponse,
    UserResponse,
    MessageResponse,
    ChatResponse,
    ConversationResponse,
    ConversationListResponse,
    ModelsListResponse,
    AssetResponse,
    AssetsListResponse,
    ChartResponse,
    DashboardResponse,
)

__all__ = [
    # Requests
    "LoginRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "ChatRequest",
    "ChatStreamRequest",
    "CreateConversationRequest",
    "UpdateConversationRequest",
    # Responses
    "TokenResponse",
    "UserResponse",
    "MessageResponse",
    "ChatResponse",
    "ConversationResponse",
    "ConversationListResponse",
    "ModelsListResponse",
    "AssetResponse",
    "AssetsListResponse",
    "ChartResponse",
    "DashboardResponse",
]