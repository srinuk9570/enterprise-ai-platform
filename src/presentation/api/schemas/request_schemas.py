"""
Pydantic models for API requests.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from uuid import UUID


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email or username")
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    
    @validator('username')
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[UUID] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ChatStreamRequest(ChatRequest):
    pass


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    model_name: str = "deepseek-r1:7b"


class UpdateConversationRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None