"""
Input validation specific exceptions.
"""
from src.domain.exceptions import DomainError


class InvalidInputError(DomainError):
    """Base class for input validation errors."""
    pass


class InvalidEmailError(InvalidInputError):
    """Raised when email format is invalid."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Invalid email format: {email}")


class InvalidUsernameError(InvalidInputError):
    """Raised when username format is invalid."""
    
    def __init__(self, username: str, reason: str):
        self.username = username
        self.reason = reason
        super().__init__(f"Invalid username '{username}': {reason}")


class WeakPasswordError(InvalidInputError):
    """Raised when password doesn't meet strength requirements."""
    
    def __init__(self, issues: list):
        self.issues = issues
        super().__init__(f"Weak password: {', '.join(issues)}")


class InvalidModelParameterError(InvalidInputError):
    """Raised when model parameter is invalid."""
    
    def __init__(self, parameter: str, value, allowed_range: str):
        self.parameter = parameter
        self.value = value
        self.allowed_range = allowed_range
        super().__init__(
            f"Invalid {parameter}: {value}. Must be {allowed_range}"
        )


class InvalidChartConfigurationError(InvalidInputError):
    """Raised when chart configuration is invalid."""
    
    def __init__(self, field: str, issue: str):
        self.field = field
        self.issue = issue
        super().__init__(f"Invalid chart configuration - {field}: {issue}")


class InvalidTimeRangeError(InvalidInputError):
    """Raised when time range is invalid."""
    
    def __init__(self, start, end, reason: str):
        self.start = start
        self.end = end
        self.reason = reason
        super().__init__(f"Invalid time range [{start} to {end}]: {reason}")


class FileTooLargeError(InvalidInputError):
    """Raised when uploaded file exceeds size limit."""
    
    def __init__(self, file_size: int, max_size: int):
        self.file_size = file_size
        self.max_size = max_size
        super().__init__(
            f"File size {file_size} bytes exceeds maximum of {max_size} bytes"
        )


class UnsupportedFileTypeError(InvalidInputError):
    """Raised when file type is not supported."""
    
    def __init__(self, file_type: str, supported_types: list):
        self.file_type = file_type
        self.supported_types = supported_types
        super().__init__(
            f"Unsupported file type '{file_type}'. "
            f"Supported: {', '.join(supported_types)}"
        )