"""
Authentication routes - login, register, refresh, logout.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

from src.presentation.api.dependencies import (
    get_dependencies,
    get_current_active_user,
    get_current_user,
)
from src.presentation.api.schemas.request_schemas import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from src.presentation.api.schemas.response_schemas import (
    TokenResponse,
    UserResponse,
    MessageResponse,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    req: Request,
    deps = Depends(get_dependencies),
):
    """
    Authenticate user and return access/refresh tokens.
    """
    # Rate limit check
    allowed, wait_time = deps.rate_limiter.check_sync(
        identifier=f"login:{request.email}",
        endpoint_type="auth",
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {wait_time}s",
        )
    
    # Authenticate
    user, error = await deps.auth_service.authenticate(
        email_or_username=request.email,
        password=request.password,
    )
    
    if not user:
        # Log failed attempt
        await deps.audit_logger.log_auth_login(
            user_id=None,
            success=False,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent"),
            failure_reason=error,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid credentials",
        )
    
    # Create tokens
    tokens = deps.jwt_handler.create_token_pair(
        user_id=user.id,
        username=user.username,
        role=user.role,
        email=str(user.email),
    )
    
    # Log successful login
    await deps.audit_logger.log_auth_login(
        user_id=user.id,
        success=True,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
    )


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    req: Request,
    deps = Depends(get_dependencies),
):
    """
    Register a new user account.
    """
    # Create user command
    from src.application.commands import CreateUserCommand
    
    command = CreateUserCommand(
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
    )
    
    user_dto, errors = await deps.user_command_handler.handle_create_user(command)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    # Log user creation
    await deps.audit_logger.log_user_created(
        user_id=UUID(user_dto.id),
        ip_address=req.client.host if req.client else None,
    )
    
    return UserResponse(
        id=user_dto.id,
        username=user_dto.username,
        email=user_dto.email,
        full_name=user_dto.full_name,
        role=user_dto.role,
        created_at=user_dto.created_at,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    deps = Depends(get_dependencies),
):
    """
    Refresh access token using refresh token.
    """
    is_valid, payload, error = deps.jwt_handler.validate_refresh_token(
        request.refresh_token
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "Invalid refresh token",
        )
    
    user_id = UUID(payload["sub"])
    user = await deps.user_repository.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Create new token pair
    tokens = deps.jwt_handler.create_token_pair(
        user_id=user.id,
        username=user.username,
        role=user.role,
        email=str(user.email),
        session_id=payload.get("session_id"),
    )
    
    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        expires_in=tokens["expires_in"],
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
    req: Request = None,
):
    """
    Logout user (blacklist token).
    """
    # Get token from Authorization header
    auth_header = req.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
        deps.jwt_handler.blacklist_token(token)
    
    # Log logout
    await deps.audit_logger.log_auth_logout(
        user_id=UUID(current_user["user_id"]),
        ip_address=req.client.host if req and req.client else None,
    )
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Get current authenticated user information.
    """
    user = await deps.user_repository.get_by_id(UUID(current_user["user_id"]))
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    from src.application.dtos import UserDTO
    user_dto = UserDTO.from_entity(user)
    
    return UserResponse(
        id=user_dto.id,
        username=user_dto.username,
        email=user_dto.email,
        full_name=user_dto.full_name,
        role=user_dto.role,
        is_active=user_dto.is_active,
        is_verified=user_dto.is_verified,
        avatar_url=user_dto.avatar_url,
        created_at=user_dto.created_at,
        last_login_at=user_dto.last_login_at,
    )


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Change user password.
    """
    from src.application.commands import UpdateUserCommand
    
    command = UpdateUserCommand(
        user_id=UUID(current_user["user_id"]),
        updated_by=UUID(current_user["user_id"]),
        current_password=request.current_password,
        new_password=request.new_password,
    )
    
    _, errors = await deps.user_command_handler.handle_update_user(command)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return MessageResponse(message="Password changed successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    deps = Depends(get_dependencies),
):
    """
    Request password reset email.
    """
    user = await deps.user_repository.get_by_email(request.email)
    
    if user:
        # Generate reset token
        token = deps.jwt_handler.create_password_reset_token(user.id)
        
        # TODO: Send email with reset link
        # For now, just return the token in development
        if deps.jwt_handler.secret_key == "dev-secret":
            return MessageResponse(
                message=f"Password reset token (dev mode): {token}"
            )
    
    # Always return success to prevent email enumeration
    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    deps = Depends(get_dependencies),
):
    """
    Reset password using token.
    """
    is_valid, user_id, error = deps.jwt_handler.verify_special_token(
        request.token,
        "password_reset",
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Invalid or expired token",
        )
    
    user = await deps.user_repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Hash new password
    new_hash = deps.password_hasher.hash(request.new_password)
    user.change_password(new_hash)
    
    await deps.user_repository.update(user)
    
    return MessageResponse(message="Password reset successfully")