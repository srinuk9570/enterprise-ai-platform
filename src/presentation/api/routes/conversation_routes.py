"""
Conversation routes - CRUD operations for conversations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID

from src.presentation.api.dependencies import (
    get_dependencies,
    get_current_active_user,
)
from src.presentation.api.schemas.request_schemas import (
    CreateConversationRequest,
    UpdateConversationRequest,
)
from src.presentation.api.schemas.response_schemas import (
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
)
from src.application.queries import GetConversationHistoryQuery, SearchConversationsQuery

router = APIRouter()


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Create a new conversation.
    """
    conv_dto, errors = await deps.conversation_command_handler.create_conversation(
        user_id=UUID(current_user["user_id"]),
        title=request.title,
        model_name=request.model_name,
    )
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return ConversationResponse(**conv_dto.to_dict())


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    List user's conversations.
    """
    dtos, total, errors = await deps.conversation_query_handler.get_user_conversations(
        user_id=UUID(current_user["user_id"]),
        skip=skip,
        limit=limit,
        status=status,
    )
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return ConversationListResponse(
        conversations=[d.to_dict() for d in dtos],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/search", response_model=ConversationListResponse)
async def search_conversations(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Search user's conversations.
    """
    query = SearchConversationsQuery(
        user_id=UUID(current_user["user_id"]),
        query=q,
        limit=limit,
    )
    
    dtos, total, errors = await deps.conversation_query_handler.handle_search_conversations(query)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return ConversationListResponse(
        conversations=[d.to_dict() for d in dtos],
        total=total,
        limit=limit,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    include_messages: bool = Query(True),
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Get a specific conversation with messages.
    """
    query = GetConversationHistoryQuery(
        conversation_id=conversation_id,
        user_id=UUID(current_user["user_id"]),
        include_messages=include_messages,
    )
    
    conv_dto, errors = await deps.conversation_query_handler.handle_get_conversation_history(query)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=errors[0],
        )
    
    return ConversationResponse(**conv_dto.to_dict())


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationRequest,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Update a conversation.
    """
    conv = await deps.conversation_repository.get_by_id(conversation_id)
    
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    
    if str(conv.user_id) != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    if request.title is not None:
        conv.update_title(request.title)
    if request.is_pinned is not None:
        conv.is_pinned = request.is_pinned
    if request.is_favorite is not None:
        conv.is_favorite = request.is_favorite
    if request.category is not None:
        conv.category = request.category
    if request.tags is not None:
        conv.tags = request.tags
    
    updated = await deps.conversation_repository.update(conv)
    
    from src.application.dtos import ConversationDTO
    return ConversationResponse(**ConversationDTO.from_entity(updated).to_dict())


@router.delete("/{conversation_id}", response_model=MessageResponse)
async def delete_conversation(
    conversation_id: UUID,
    permanent: bool = Query(False),
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Delete a conversation.
    """
    from src.application.commands import DeleteConversationCommand
    
    command = DeleteConversationCommand(
        conversation_id=conversation_id,
        user_id=UUID(current_user["user_id"]),
        permanent=permanent,
    )
    
    success, errors = await deps.conversation_command_handler.handle_delete_conversation(command)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return MessageResponse(message="Conversation deleted successfully")


@router.post("/{conversation_id}/archive", response_model=MessageResponse)
async def archive_conversation(
    conversation_id: UUID,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Archive a conversation.
    """
    from src.application.commands import ArchiveConversationCommand
    
    command = ArchiveConversationCommand(
        conversation_id=conversation_id,
        user_id=UUID(current_user["user_id"]),
        archive=True,
    )
    
    success, errors = await deps.conversation_command_handler.handle_archive_conversation(command)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return MessageResponse(message="Conversation archived successfully")