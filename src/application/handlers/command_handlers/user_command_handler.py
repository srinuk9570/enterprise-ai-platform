"""
Handler for user-related commands.
"""
from typing import Optional, Tuple
from uuid import UUID
import logging

from src.application.commands import (
    CreateUserCommand,
    UpdateUserCommand,
)
from src.application.dtos import UserDTO
from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.domain.services.authentication_service import AuthenticationService
from src.domain.exceptions import (
    DomainValidationError,
    EntityNotFoundError,
    UnauthorizedOperationError,
    DuplicateEntityError,
)
from src.shared.constants import UserRole

logger = logging.getLogger(__name__)


class UserCommandHandler:
    """
    Handler for user-related commands.
    """
    
    def __init__(
        self,
        user_repository,
        authentication_service: AuthenticationService,
        event_bus=None,
    ):
        self.user_repository = user_repository
        self.auth_service = authentication_service
        self.event_bus = event_bus
    
    async def handle_create_user(self, command: CreateUserCommand) -> Tuple[Optional[UserDTO], list[str]]:
        """
        Handle CreateUserCommand.
        Returns (user_dto, errors).
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Check if can register
            can_register, error = await self.auth_service.can_register(
                email=command.email,
                username=command.username,
            )
            
            if not can_register:
                return None, [error]
            
            # Create user entity
            email_vo = Email(command.email)
            hashed_password = self.auth_service.hash_password(command.password)
            
            role = UserRole(command.role) if command.role else UserRole.USER
            
            user = User(
                email=email_vo,
                username=command.username,
                hashed_password=hashed_password,
                full_name=command.full_name,
                role=role,
                is_verified=command.auto_verify,
            )
            
            # Save user
            created_user = await self.user_repository.add(user)
            
            # Publish event if event bus exists
            if self.event_bus:
                await self.event_bus.publish("user.created", {
                    "user_id": str(created_user.id),
                    "email": str(created_user.email),
                    "username": created_user.username,
                    "send_verification": command.send_verification_email,
                })
            
            logger.info(f"User created: {created_user.username} ({created_user.id})")
            
            return UserDTO.from_entity(created_user), []
            
        except DomainValidationError as e:
            return None, [str(e)]
        except DuplicateEntityError as e:
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None, ["Internal server error"]
    
    async def handle_update_user(self, command: UpdateUserCommand) -> Tuple[Optional[UserDTO], list[str]]:
        """
        Handle UpdateUserCommand.
        Returns (updated_user_dto, errors).
        """
        # Validate command
        is_valid, errors = command.validate()
        if not is_valid:
            return None, errors
        
        try:
            # Get user
            user = await self.user_repository.get_by_id(command.user_id)
            if not user:
                raise EntityNotFoundError("User", str(command.user_id))
            
            # Get updating user (for permission check)
            updater = await self.user_repository.get_by_id(command.updated_by)
            if not updater:
                raise EntityNotFoundError("User", str(command.updated_by))
            
            # Check permissions
            if not user.can_modify_resource(command.updated_by) and updater.role != UserRole.ADMIN:
                raise UnauthorizedOperationError("You don't have permission to update this user")
            
            # Handle profile updates
            if command.has_profile_updates():
                email_vo = Email(command.email) if command.email else None
                
                user.update_profile(
                    full_name=command.full_name,
                    email=email_vo,
                    bio=command.bio,
                    avatar_url=command.avatar_url,
                )
            
            # Handle password change
            if command.has_password_change():
                # Verify current password
                if not self.auth_service.password_hasher.verify(
                    command.current_password,
                    user.hashed_password,
                ):
                    return None, ["Current password is incorrect"]
                
                # Validate new password strength
                is_valid, issues = self.auth_service.validate_password_strength(command.new_password)
                if not is_valid:
                    return None, issues
                
                new_hash = self.auth_service.hash_password(command.new_password)
                user.change_password(new_hash)
            
            # Handle role change
            if command.has_role_change():
                new_role = UserRole(command.new_role)
                if updater.role == UserRole.ADMIN:
                    if new_role == UserRole.ADMIN and user.role != UserRole.ADMIN:
                        user.promote_to_role(new_role, promoted_by=updater)
                    else:
                        user.role = new_role
                else:
                    return None, ["Only admins can change user roles"]
            
            # Handle preferences update
            if command.preferences:
                user.update_preferences(command.preferences)
            
            # Save updates
            updated_user = await self.user_repository.update(user)
            
            # Publish event
            if self.event_bus:
                await self.event_bus.publish("user.updated", {
                    "user_id": str(updated_user.id),
                    "updated_by": str(command.updated_by),
                    "changes": {
                        "profile": command.has_profile_updates(),
                        "password": command.has_password_change(),
                        "role": command.has_role_change(),
                        "preferences": command.preferences is not None,
                    },
                })
            
            logger.info(f"User updated: {updated_user.id} by {command.updated_by}")
            
            return UserDTO.from_entity(updated_user), []
            
        except EntityNotFoundError as e:
            return None, [str(e)]
        except UnauthorizedOperationError as e:
            return None, [str(e)]
        except DomainValidationError as e:
            return None, [str(e)]
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None, ["Internal server error"]
    
    async def handle_delete_user(self, user_id: UUID, deleted_by: UUID) -> Tuple[bool, list[str]]:
        """
        Handle user deletion (admin only).
        """
        try:
            # Get users
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise EntityNotFoundError("User", str(user_id))
            
            deleter = await self.user_repository.get_by_id(deleted_by)
            if not deleter:
                raise EntityNotFoundError("User", str(deleted_by))
            
            # Check permissions
            if deleter.role != UserRole.ADMIN:
                raise UnauthorizedOperationError("Only admins can delete users")
            
            if user.role == UserRole.ADMIN:
                # Count remaining admins
                admins = await self.user_repository.get_users_by_role(UserRole.ADMIN)
                if len(admins) <= 1:
                    return False, ["Cannot delete the last admin user"]
            
            # Delete user
            success = await self.user_repository.delete(user_id)
            
            if success and self.event_bus:
                await self.event_bus.publish("user.deleted", {
                    "user_id": str(user_id),
                    "deleted_by": str(deleted_by),
                })
            
            logger.info(f"User deleted: {user_id} by {deleted_by}")
            
            return success, []
            
        except EntityNotFoundError as e:
            return False, [str(e)]
        except UnauthorizedOperationError as e:
            return False, [str(e)]
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False, ["Internal server error"]