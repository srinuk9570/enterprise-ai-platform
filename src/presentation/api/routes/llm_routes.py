"""
LLM routes - chat, streaming, models.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID

from src.presentation.api.dependencies import (
    get_dependencies,
    get_current_active_user,
)
from src.application.commands import SendMessageCommand
from src.application.queries import StreamChatResponseQuery
from src.presentation.api.schemas.request_schemas import (
    ChatRequest,
    ChatStreamRequest,
)
from src.presentation.api.schemas.response_schemas import (
    ChatResponse,
    ModelsListResponse,
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Send a message to the AI and get a response.
    """
    # Create or get conversation
    conversation_id = request.conversation_id
    
    if not conversation_id:
        # Create new conversation
        conv_dto, errors = await deps.conversation_command_handler.create_conversation(
            user_id=UUID(current_user["user_id"]),
            model_name=request.model or deps.ollama_client.default_model,
        )
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors[0],
            )
        conversation_id = UUID(conv_dto.id)
    
    # Send message command
    command = SendMessageCommand(
        conversation_id=conversation_id,
        content=request.message,
        user_id=UUID(current_user["user_id"]),
        model_name=request.model,
        model_parameters=request.parameters,
        system_prompt=request.system_prompt,
        stream_response=False,
    )
    
    response_dto, errors = await deps.conversation_command_handler.handle_send_message(command)
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=errors[0],
        )
    
    return ChatResponse(
        conversation_id=str(conversation_id),
        message=response_dto.content,
        model_used=response_dto.model_used,
        tokens_used=response_dto.tokens_used,
        generation_time_ms=response_dto.generation_time_ms,
        finish_reason=response_dto.finish_reason,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatStreamRequest,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Stream a chat response using Server-Sent Events.
    """
    conversation_id = request.conversation_id
    
    if not conversation_id:
        # Create new conversation
        conv_dto, errors = await deps.conversation_command_handler.create_conversation(
            user_id=UUID(current_user["user_id"]),
            model_name=request.model or deps.ollama_client.default_model,
        )
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors[0],
            )
        conversation_id = UUID(conv_dto.id)
    
    command = SendMessageCommand(
        conversation_id=conversation_id,
        content=request.message,
        user_id=UUID(current_user["user_id"]),
        model_name=request.model,
        model_parameters=request.parameters,
        system_prompt=request.system_prompt,
        stream_response=True,
    )
    
    async def generate():
        # Send conversation ID first
        yield f"data: {json.dumps({'conversation_id': str(conversation_id)})}\n\n"
        
        # Stream response
        async for chunk in deps.conversation_command_handler.handle_stream_message(command):
            yield deps.streaming_handler.format_sse_chunk(chunk)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models", response_model=ModelsListResponse)
async def list_models(
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    List available LLM models.
    """
    models = await deps.ollama_client.list_models()
    
    # Get model info from registry
    model_infos = []
    for model_name in models:
        info = deps.model_registry.get_model_info(model_name)
        if info:
            model_infos.append(info.to_dict())
        else:
            model_infos.append({
                "name": model_name,
                "display_name": model_name,
                "capabilities": ["chat"],
            })
    
    return ModelsListResponse(models=model_infos, total=len(model_infos))


@router.get("/models/{model_name}")
async def get_model_info(
    model_name: str,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Get detailed information about a specific model.
    """
    info = await deps.ollama_client.get_model_info(model_name)
    
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found",
        )
    
    return info


@router.post("/models/pull")
async def pull_model(
    model_name: str,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Pull a new model from Ollama registry (admin only).
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    
    success = await deps.ollama_client.pull_model(model_name)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pull model '{model_name}'",
        )
    
    return {"message": f"Model '{model_name}' pulled successfully"}


@router.get("/prompts/templates")
async def list_prompt_templates(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    List available prompt templates.
    """
    templates = deps.prompt_template_manager.list_templates(category)
    return {
        "templates": [t.to_dict() for t in templates],
        "total": len(templates),
        "categories": deps.prompt_template_manager.list_categories(),
    }


@router.post("/prompts/render")
async def render_prompt(
    template_name: str,
    variables: Dict[str, Any],
    current_user: dict = Depends(get_current_active_user),
    deps = Depends(get_dependencies),
):
    """
    Render a prompt template with variables.
    """
    try:
        rendered = deps.prompt_template_manager.render(template_name, **variables)
        return {"rendered": rendered}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )