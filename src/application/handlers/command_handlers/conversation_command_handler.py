"""
Handler for conversation-related commands.
"""
from typing import Optional, Tuple
from uuid import UUID
import logging

from src.application.commands import (
    SendMessageCommand,
    DeleteConversationCommand,
    ArchiveConversationCommand,
)
from src.application.dtos import MessageDTO, ConversationDTO, LLMResponseDTO
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.services.llm_orchestration_service import LLMOrchestrationService
from src.domain.value_objects.model_parameters import ModelParameters
from src.domain.exceptions import (
    EntityNotFoundError,
    UnauthorizedOperationError,
    BusinessRuleViolationError,
    TokenLimitExceededError,
    ModelNotAvailableError,
)
from src.shared.constants import MessageRole, ConversationStatus

logger = logging.getLogger(__name__)


class ConversationCommandHandler:
    """
    Handler for conversation-related commands.
    """
    
    def __init__(
        self,
        conversation_repository,
        message_repository,
        llm_service: LLMOrchestrationService,
        user_repository,
        event_bus=None,
    ):
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository
        self.llm_service = llm_service
        self.user_repository = user_repository
        self.event_bus = event_bus
    
    async def handle_send_message(
        self,
        command: SendMessageCommand,
    ) -> Tuple[Optional[LLMResponseDTO], list[str]]:
        """
        Handle SendMessageCommand.
        Returns (response_dto, errors).
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Get conversation
            conversation = await self.conversation_repository.get_conversation_with_messages(
                command.conversation_id
            )
            if not conversation:
                raise EntityNotFoundError("Conversation", str(command.conversation_id))
            
            # Check permissions
            if not self._can_access_conversation(conversation, command.user_id):
                raise UnauthorizedOperationError("You don't have access to this conversation")
            
            # Check conversation status
            if conversation.status != ConversationStatus.ACTIVE:
                return None, [f"Cannot send message to {conversation.status.value} conversation"]
            
            # Update model if specified
            if command.model_name:
                conversation.model_name = command.model_name
            
            # Set system prompt if specified
            if command.system_prompt:
                conversation.set_system_prompt(command.system_prompt)
            
            # Parse model parameters
            parameters = None
            if command.model_parameters:
                parameters = ModelParameters(**command.model_parameters)
            
            # Generate response
            if command.stream_response:
                # Streaming handled separately
                response_dto = LLMResponseDTO(
                    content="",
                    model_used=conversation.model_name,
                    tokens_used=0,
                    generation_time_ms=0,
                    finish_reason="streaming",
                    streaming=True,
                )
            else:
                response = await self.llm_service.generate_response(
                    conversation=conversation,
                    user_message=command.content,
                    parameters=parameters,
                    system_prompt=command.system_prompt,
                )
                
                response_dto = LLMResponseDTO.from_entity(response)
            
            # Save conversation updates
            await self.conversation_repository.update(conversation)
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish("message.sent", {
                    "conversation_id": str(conversation.id),
                    "user_id": str(command.user_id),
                    "message_length": len(command.content),
                    "model_used": conversation.model_name,
                })
            
            logger.info(f"Message sent in conversation {conversation.id}")
            
            return response_dto, []
            
        except EntityNotFoundError as e:
            return None, [str(e)]
        except UnauthorizedOperationError as e:
            return None, [str(e)]
        except TokenLimitExceededError as e:
            return None, [f"Token limit exceeded: {e}"]
        except ModelNotAvailableError as e:
            return None, [f"Model not available: {e.model_name}"]
        except BusinessRuleViolationError as e:
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None, ["Internal server error"]
    
    async def handle_stream_message(
        self,
        command: SendMessageCommand,
    ):
        """
        Handle streaming message generation.
        Yields response chunks.
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            yield f"Error: {errors[0]}"
            return
        
        try:
            # Get conversation
            conversation = await self.conversation_repository.get_conversation_with_messages(
                command.conversation_id
            )
            if not conversation:
                yield "Error: Conversation not found"
                return
            
            # Check permissions
            if not self._can_access_conversation(conversation, command.user_id):
                yield "Error: Unauthorized"
                return
            
            # Parse parameters
            parameters = None
            if command.model_parameters:
                parameters = ModelParameters(**command.model_parameters)
            
            # Stream response
            async for chunk in self.llm_service.generate_streaming_response(
                conversation=conversation,
                user_message=command.content,
                parameters=parameters,
                system_prompt=command.system_prompt,
            ):
                yield chunk
            
            # Save conversation updates
            await self.conversation_repository.update(conversation)
            
        except TokenLimitExceededError:
            yield "Error: Token limit exceeded"
        except ModelNotAvailableError:
            yield "Error: Model not available"
        except Exception as e:
            logger.error(f"Error streaming message: {e}")
            yield f"Error: {str(e)}"
    
    async def handle_delete_conversation(
        self,
        command: DeleteConversationCommand,
    ) -> Tuple[bool, list[str]]:
        """
        Handle DeleteConversationCommand.
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return False, errors
        
        try:
            # Get conversation
            conversation = await self.conversation_repository.get_by_id(command.conversation_id)
            if not conversation:
                raise EntityNotFoundError("Conversation", str(command.conversation_id))
            
            # Check permissions
            if not self._can_modify_conversation(conversation, command.user_id):
                raise UnauthorizedOperationError("You don't have permission to delete this conversation")
            
            if command.permanent:
                # Hard delete
                success = await self.conversation_repository.delete(command.conversation_id)
                
                # TODO: Delete associated assets if command.delete_assets
                
                action = "permanently deleted"
            else:
                # Soft delete
                conversation.delete()
                await self.conversation_repository.update(conversation)
                success = True
                action = "soft deleted"
            
            # Publish event
            if success and self.event_bus:
                await self.event_bus.publish("conversation.deleted", {
                    "conversation_id": str(command.conversation_id),
                    "user_id": str(command.user_id),
                    "permanent": command.permanent,
                })
            
            logger.info(f"Conversation {action}: {command.conversation_id}")
            
            return success, []
            
        except EntityNotFoundError as e:
            return False, [str(e)]
        except UnauthorizedOperationError as e:
            return False, [str(e)]
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return False, ["Internal server error"]
    
    async def handle_archive_conversation(
        self,
        command: ArchiveConversationCommand,
    ) -> Tuple[bool, list[str]]:
        """
        Handle ArchiveConversationCommand.
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return False, errors
        
        try:
            # Get conversation
            conversation = await self.conversation_repository.get_by_id(command.conversation_id)
            if not conversation:
                raise EntityNotFoundError("Conversation", str(command.conversation_id))
            
            # Check permissions
            if not self._can_modify_conversation(conversation, command.user_id):
                raise UnauthorizedOperationError("You don't have permission to archive this conversation")
            
            if command.archive:
                conversation.archive()
                action = "archived"
            else:
                conversation.unarchive()
                action = "unarchived"
            
            await self.conversation_repository.update(conversation)
            
            logger.info(f"Conversation {action}: {command.conversation_id}")
            
            return True, []
            
        except EntityNotFoundError as e:
            return False, [str(e)]
        except UnauthorizedOperationError as e:
            return False, [str(e)]
        except Exception as e:
            logger.error(f"Error archiving conversation: {e}")
            return False, ["Internal server error"]
    
    async def create_conversation(
        self,
        user_id: UUID,
        title: Optional[str] = None,
        model_name: str = "deepseek-r1:7b",
    ) -> Tuple[Optional[ConversationDTO], list[str]]:
        """
        Create a new conversation.
        """
        try:
            # Get user
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                return None, ["User not found"]
            
            # Check conversation limit
            user_conversations = await self.conversation_repository.get_active_conversations(user_id)
            if len(user_conversations) >= user.get_conversation_limit():
                return None, [f"Conversation limit reached ({user.get_conversation_limit()})"]
            
            # Generate title if not provided
            if not title:
                title = f"New Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            
            # Create conversation
            conversation = Conversation(
                user_id=user_id,
                title=title,
                model_name=model_name,
            )
            
            created = await self.conversation_repository.add(conversation)
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish("conversation.created", {
                    "conversation_id": str(created.id),
                    "user_id": str(user_id),
                    "model_name": model_name,
                })
            
            logger.info(f"Conversation created: {created.id}")
            
            return ConversationDTO.from_entity(created), []
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None, ["Internal server error"]
    
    def _can_access_conversation(self, conversation: Conversation, user_id: UUID) -> bool:
        """Check if user can access conversation."""
        return conversation.user_id == user_id
    
    def _can_modify_conversation(self, conversation: Conversation, user_id: UUID) -> bool:
        """Check if user can modify conversation."""
        return conversation.user_id == user_id


# Import for datetime in create_conversation
from datetime import datetime