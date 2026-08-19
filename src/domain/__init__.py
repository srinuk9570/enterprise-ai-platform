"""
Domain Layer - Pure Business Logic
Contains entities, value objects, repositories (abstract), and domain services.
No external dependencies or framework code allowed here.
"""
from src.domain.entities.user import User
from src.domain.entities.conversation import Conversation
from src.domain.entities.message import Message
from src.domain.entities.chart_configuration import ChartConfiguration
from src.domain.entities.generated_asset import GeneratedAsset

from src.domain.value_objects.email import Email
from src.domain.value_objects.api_key import ApiKey
from src.domain.value_objects.model_parameters import ModelParameters
from src.domain.value_objects.time_range import TimeRange

from src.domain.exceptions import (
    DomainError,
    DomainValidationError,
    EntityNotFoundError,
    UnauthorizedOperationError,
    InvalidStateTransitionError,
    BusinessRuleViolationError,
)

__all__ = [
    # Entities
    "User",
    "Conversation",
    "Message",
    "ChartConfiguration",
    "GeneratedAsset",
    # Value Objects
    "Email",
    "ApiKey",
    "ModelParameters",
    "TimeRange",
    # Exceptions
    "DomainError",
    "DomainValidationError",
    "EntityNotFoundError",
    "UnauthorizedOperationError",
    "InvalidStateTransitionError",
    "BusinessRuleViolationError",
]