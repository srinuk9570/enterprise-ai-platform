"""
Pydantic models for API responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool = True
    is_verified: bool = False
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    last_login_at: Optional[str] = None


class MessageResponse(BaseModel):
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    model_used: str
    tokens_used: int
    generation_time_ms: float
    finish_reason: str


class ConversationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    model_name: str
    status: str
    created_at: str
    updated_at: str
    system_prompt: Optional[str] = None
    tags: List[str] = []
    is_pinned: bool = False
    is_favorite: bool = False
    total_tokens: int = 0
    message_count: int = 0
    messages: Optional[List[Dict[str, Any]]] = None
    last_message: Optional[Dict[str, Any]] = None


class ConversationListResponse(BaseModel):
    conversations: List[Dict[str, Any]]
    total: int
    skip: int = 0
    limit: int = 50


class ModelInfoResponse(BaseModel):
    name: str
    display_name: str
    capabilities: List[str] = []
    context_length: int = 4096
    description: str = ""


class ModelsListResponse(BaseModel):
    models: List[Dict[str, Any]]
    total: int


class AssetResponse(BaseModel):
    id: str
    user_id: str
    asset_type: str
    file_name: str
    file_size: int
    formatted_file_size: str
    mime_type: str
    created_at: str
    title: Optional[str] = None
    prompt: Optional[str] = None
    model_used: Optional[str] = None
    tags: List[str] = []
    is_favorite: bool = False
    is_public: bool = False
    view_count: int = 0
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class AssetsListResponse(BaseModel):
    assets: List[Dict[str, Any]]
    total: int
    skip: int = 0
    limit: int = 50


class ChartResponse(BaseModel):
    id: str
    name: str
    chart_type: str
    asset: AssetResponse
    data: Optional[Dict[str, Any]] = None


class DashboardResponse(BaseModel):
    user: Dict[str, Any]
    period: str
    conversations: Dict[str, Any]
    assets: Dict[str, Any]
    usage: Dict[str, Any]
    recent_conversations: List[Dict[str, Any]] = []
    recent_assets: List[Dict[str, Any]] = []