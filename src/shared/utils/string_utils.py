"""
String manipulation utility functions.
"""
import re
import json
import secrets
import string
from typing import Optional, Any, List


def slugify(text: str, separator: str = "-") -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
        separator: Word separator
    
    Returns:
        Slug string
    """
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with separator
    text = re.sub(r"\s+", separator, text)
    
    # Remove non-alphanumeric characters
    text = re.sub(rf"[^a-z0-9{separator}]", "", text)
    
    # Remove consecutive separators
    text = re.sub(rf"{separator}+", separator, text)
    
    # Trim separators
    text = text.strip(separator)
    
    return text


def truncate(
    text: str,
    max_length: int,
    ellipsis: str = "...",
    preserve_words: bool = True,
) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        ellipsis: Ellipsis string
        preserve_words: Don't cut words in half
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(ellipsis)]
    
    if preserve_words:
        last_space = truncated.rfind(" ")
        if last_space > max_length // 2:
            truncated = truncated[:last_space]
    
    return truncated + ellipsis


def mask_email(email: str, visible_chars: int = 2) -> str:
    """
    Mask an email address for privacy.
    
    Args:
        email: Email address
        visible_chars: Number of characters to show
    
    Returns:
        Masked email
    """
    if "@" not in email:
        return mask_string(email, visible_chars)
    
    local, domain = email.split("@", 1)
    
    if len(local) <= visible_chars:
        masked_local = local[0] + "*" * (len(local) - 1)
    else:
        masked_local = local[:visible_chars] + "*" * (len(local) - visible_chars)
    
    return f"{masked_local}@{domain}"


def mask_string(text: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask a string for privacy.
    
    Args:
        text: String to mask
        visible_chars: Number of characters to show at start and end
        mask_char: Character to use for masking
    
    Returns:
        Masked string
    """
    if len(text) <= visible_chars * 2:
        return mask_char * len(text)
    
    start = text[:visible_chars]
    end = text[-visible_chars:]
    middle = mask_char * (len(text) - visible_chars * 2)
    
    return f"{start}{middle}{end}"


def generate_random_string(
    length: int = 32,
    include_upper: bool = True,
    include_lower: bool = True,
    include_digits: bool = True,
    include_special: bool = False,
) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: String length
        include_upper: Include uppercase letters
        include_lower: Include lowercase letters
        include_digits: Include digits
        include_special: Include special characters
    
    Returns:
        Random string
    """
    alphabet = ""
    
    if include_lower:
        alphabet += string.ascii_lowercase
    if include_upper:
        alphabet += string.ascii_uppercase
    if include_digits:
        alphabet += string.digits
    if include_special:
        alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    if not alphabet:
        alphabet = string.ascii_letters + string.digits
    
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_id(prefix: str = "", length: int = 16) -> str:
    """
    Generate a short unique ID.
    
    Args:
        prefix: Optional prefix
        length: ID length
    
    Returns:
        Unique ID string
    """
    alphabet = string.ascii_lowercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def camel_to_snake(text: str) -> str:
    """
    Convert camelCase to snake_case.
    
    Args:
        text: camelCase string
    
    Returns:
        snake_case string
    """
    # Insert underscore before capital letters
    text = re.sub(r"(?<!^)(?=[A-Z])", "_", text)
    return text.lower()


def snake_to_camel(text: str, upper_first: bool = False) -> str:
    """
    Convert snake_case to camelCase.
    
    Args:
        text: snake_case string
        upper_first: Capitalize first letter (PascalCase)
    
    Returns:
        camelCase or PascalCase string
    """
    parts = text.split("_")
    
    if upper_first:
        return "".join(p.capitalize() for p in parts)
    else:
        return parts[0] + "".join(p.capitalize() for p in parts[1:])


def parse_boolean(value: Any, default: bool = False) -> bool:
    """
    Parse a value to boolean.
    
    Args:
        value: Value to parse
        default: Default value
    
    Returns:
        Boolean value
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ("true", "yes", "1", "on", "y"):
            return True
        if value_lower in ("false", "no", "0", "off", "n"):
            return False
    
    if isinstance(value, (int, float)):
        return bool(value)
    
    return default


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        json_str: JSON string
        default: Default value if parsing fails
    
    Returns:
        Parsed object or default
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: Any = None, **kwargs) -> str:
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        default: Default value if serialization fails
        **kwargs: Additional json.dumps arguments
    
    Returns:
        JSON string or default
    """
    try:
        return json.dumps(obj, **kwargs)
    except (TypeError, ValueError):
        return default if default is not None else "{}"


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to search
    
    Returns:
        List of email addresses
    """
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(pattern, text)


def extract_urls(text: str) -> List[str]:
    """
    Extract URLs from text.
    
    Args:
        text: Text to search
    
    Returns:
        List of URLs
    """
    pattern = r"https?://[^\s<>\"']+|www\.[^\s<>\"']+"
    return re.findall(pattern, text)


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text to search
    
    Returns:
        List of hashtags (without #)
    """
    pattern = r"#(\w+)"
    return re.findall(pattern, text)


def highlight_text(
    text: str,
    query: str,
    tag: str = "mark",
    css_class: str = "highlight",
) -> str:
    """
    Highlight search terms in text.
    
    Args:
        text: Text to highlight
        query: Search query
        tag: HTML tag to use
        css_class: CSS class for highlight
    
    Returns:
        HTML with highlighted text
    """
    if not query or not text:
        return text
    
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    replacement = f'<{tag} class="{css_class}">\\g<0></{tag}>'
    return pattern.sub(replacement, text)


def word_count(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count
    
    Returns:
        Word count
    """
    return len(text.split())


def reading_time_minutes(text: str, words_per_minute: int = 200) -> float:
    """
    Estimate reading time.
    
    Args:
        text: Text to estimate
        words_per_minute: Reading speed
    
    Returns:
        Estimated minutes
    """
    words = word_count(text)
    return words / words_per_minute