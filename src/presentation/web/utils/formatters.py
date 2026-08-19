"""
Formatting utilities for consistent data display.
"""
from datetime import datetime, timedelta
from typing import Optional, Union, List, Dict, Any
import math


def format_date(
    date: Optional[Union[datetime, str]],
    format: str = "%Y-%m-%d",
    default: str = "N/A",
) -> str:
    """
    Format a date for display.
    
    Args:
        date: Date to format (datetime or ISO string)
        format: Output format string
        default: Default value if date is None
    
    Returns:
        Formatted date string
    """
    if date is None:
        return default
    
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return default
    
    if isinstance(date, datetime):
        return date.strftime(format)
    
    return default


def format_datetime(
    dt: Optional[Union[datetime, str]],
    include_time: bool = True,
    relative: bool = False,
    default: str = "N/A",
) -> str:
    """
    Format a datetime with smart relative display.
    
    Args:
        dt: Datetime to format
        include_time: Whether to include time
        relative: Use relative format (e.g., "2 hours ago")
        default: Default value if None
    
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return default
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return default
    
    if not isinstance(dt, datetime):
        return default
    
    if relative:
        return _format_relative_time(dt)
    
    if include_time:
        if dt.date() == datetime.utcnow().date():
            return f"Today at {dt.strftime('%H:%M')}"
        elif dt.date() == (datetime.utcnow() - timedelta(days=1)).date():
            return f"Yesterday at {dt.strftime('%H:%M')}"
        else:
            return dt.strftime("%Y-%m-%d %H:%M")
    else:
        return dt.strftime("%Y-%m-%d")


def _format_relative_time(dt: datetime) -> str:
    """Format relative time (e.g., '2 hours ago')."""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.total_seconds() < 0:
        return "just now"
    
    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.days < 7:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"


def format_number(
    value: Optional[Union[int, float]],
    decimals: int = 0,
    thousands_sep: str = ",",
    default: str = "0",
) -> str:
    """
    Format a number with thousand separators.
    
    Args:
        value: Number to format
        decimals: Decimal places
        thousands_sep: Thousands separator
        default: Default value if None
    
    Returns:
        Formatted number string
    """
    if value is None:
        return default
    
    if decimals > 0:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{int(value):,}"
    
    if thousands_sep != ",":
        formatted = formatted.replace(",", thousands_sep)
    
    return formatted


def format_file_size(size_bytes: Optional[int], binary: bool = True) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        binary: Use binary units (KiB, MiB) vs decimal (KB, MB)
    
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes is None or size_bytes < 0:
        return "0 B"
    
    if binary:
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        factor = 1024
    else:
        units = ["B", "KB", "MB", "GB", "TB"]
        factor = 1000
    
    size = float(size_bytes)
    unit_index = 0
    
    while size >= factor and unit_index < len(units) - 1:
        size /= factor
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def format_duration(seconds: Optional[float], show_seconds: bool = True) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        show_seconds: Whether to show seconds
    
    Returns:
        Formatted duration (e.g., "2h 30m")
    """
    if seconds is None or seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:
        parts.append(f"{minutes}m")
    if show_seconds and (secs > 0 or not parts):
        parts.append(f"{secs}s")
    
    return " ".join(parts) if parts else "0s"


def format_tokens(count: Optional[int]) -> str:
    """
    Format token count for display.
    
    Args:
        count: Token count
    
    Returns:
        Formatted token count
    """
    if count is None:
        return "0"
    
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1000000:.1f}M"


def truncate_text(
    text: Optional[str],
    max_length: int = 100,
    ellipsis: str = "...",
    preserve_words: bool = True,
) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        ellipsis: Ellipsis string
        preserve_words: Don't cut words in half
    
    Returns:
        Truncated text
    """
    if text is None:
        return ""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length - len(ellipsis)]
    
    if preserve_words:
        last_space = truncated.rfind(" ")
        if last_space > max_length // 2:
            truncated = truncated[:last_space]
    
    return truncated + ellipsis


def format_conversation_title(
    title: Optional[str],
    first_message: Optional[str] = None,
    default: str = "New Conversation",
) -> str:
    """
    Format conversation title for display.
    
    Args:
        title: Existing title
        first_message: First message content
        default: Default title
    
    Returns:
        Formatted title
    """
    if title and title.strip():
        return truncate_text(title.strip(), 50)
    
    if first_message:
        return truncate_text(first_message.strip(), 40)
    
    return default


def format_model_name(model_name: str) -> str:
    """
    Format model name for display.
    
    Args:
        model_name: Raw model name (e.g., "deepseek-r1:7b")
    
    Returns:
        Display name (e.g., "DeepSeek R1 7B")
    """
    # Common model name mappings
    mappings = {
        "deepseek-r1": "DeepSeek R1",
        "llama3.2": "Llama 3.2",
        "qwen2.5": "Qwen 2.5",
        "mistral": "Mistral",
        "codellama": "Code Llama",
    }
    
    # Remove tag and version
    base_name = model_name.split(":")[0]
    
    # Apply mapping
    for key, display in mappings.items():
        if key in base_name.lower():
            # Add size if present
            if ":7b" in model_name:
                return f"{display} 7B"
            elif ":14b" in model_name:
                return f"{display} 14B"
            elif ":3b" in model_name:
                return f"{display} 3B"
            return display
    
    return model_name.replace("-", " ").title()


def format_role(role: str) -> str:
    """
    Format user role for display.
    
    Args:
        role: Raw role string
    
    Returns:
        Display role
    """
    role_map = {
        "admin": "Administrator",
        "power_user": "Power User",
        "user": "User",
        "viewer": "Viewer",
    }
    return role_map.get(role.lower(), role.title())


def get_initials(name: str, max_length: int = 2) -> str:
    """
    Get initials from a name.
    
    Args:
        name: Full name or username
        max_length: Maximum number of initials
    
    Returns:
        Initials (e.g., "JD")
    """
    if not name:
        return "?"
    
    parts = name.strip().split()
    
    if len(parts) >= 2:
        initials = "".join(p[0].upper() for p in parts[:max_length] if p)
    else:
        initials = name[:max_length].upper()
    
    return initials


def format_percentage(
    value: Optional[float],
    decimals: int = 1,
    include_sign: bool = False,
) -> str:
    """
    Format a value as percentage.
    
    Args:
        value: Value (0-1 or 0-100)
        decimals: Decimal places
        include_sign: Include % sign
    
    Returns:
        Formatted percentage
    """
    if value is None:
        return "N/A"
    
    # Detect if value is already percentage
    if value > 1 and value <= 100:
        percentage = value
    else:
        percentage = value * 100
    
    formatted = f"{percentage:.{decimals}f}"
    
    if include_sign:
        formatted += "%"
    
    return formatted


def format_countdown(seconds: int) -> str:
    """
    Format countdown timer.
    
    Args:
        seconds: Seconds remaining
    
    Returns:
        Formatted countdown (e.g., "02:30")
    """
    if seconds < 0:
        seconds = 0
    
    minutes = seconds // 60
    secs = seconds % 60
    
    return f"{minutes:02d}:{secs:02d}"


def format_list(
    items: List[Any],
    separator: str = ", ",
    last_separator: str = " and ",
    max_items: int = 5,
    truncate_msg: str = "...",
) -> str:
    """
    Format a list as a string.
    
    Args:
        items: List of items
        separator: Separator between items
        last_separator: Separator before last item
        max_items: Maximum items to show
        truncate_msg: Message for truncated items
    
    Returns:
        Formatted list string
    """
    if not items:
        return ""
    
    str_items = [str(item) for item in items]
    
    if len(str_items) > max_items:
        shown = str_items[:max_items]
        remaining = len(str_items) - max_items
        return separator.join(shown) + f" {truncate_msg} ({remaining} more)"
    
    if len(str_items) == 1:
        return str_items[0]
    
    if len(str_items) == 2:
        return f"{str_items[0]}{last_separator}{str_items[1]}"
    
    return separator.join(str_items[:-1]) + last_separator + str_items[-1]