"""
General helper utilities for the web application.
"""
import hashlib
import json
import time
import base64
import uuid
from typing import Optional, Any, Callable, List, Dict, TypeVar, Iterator
from functools import wraps
from pathlib import Path
import streamlit as st
from datetime import datetime
import threading

T = TypeVar("T")


# ==================== ID Generation ====================

def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a short unique ID.
    
    Args:
        prefix: Optional prefix
        length: ID length
    
    Returns:
        Unique ID string
    """
    import secrets
    import string
    
    alphabet = string.ascii_lowercase + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(length))
    
    if prefix:
        return f"{prefix}_{random_part}"
    return random_part


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_session_id() -> str:
    """Generate a session ID."""
    return hashlib.sha256(f"{time.time()}_{uuid.uuid4()}".encode()).hexdigest()[:16]


# ==================== Debounce & Throttle ====================

def debounce(wait: float):
    """
    Debounce decorator - delays function execution until after wait period.
    
    Args:
        wait: Wait time in seconds
    
    Usage:
        @debounce(0.5)
        def on_input_change(value):
            ...
    """
    def decorator(func: Callable) -> Callable:
        timer: Optional[threading.Timer] = None
        
        @wraps(func)
        def debounced(*args, **kwargs):
            nonlocal timer
            
            if timer is not None:
                timer.cancel()
            
            timer = threading.Timer(wait, lambda: func(*args, **kwargs))
            timer.start()
        
        return debounced
    return decorator


def throttle(wait: float):
    """
    Throttle decorator - limits function execution to once per wait period.
    
    Args:
        wait: Minimum time between calls in seconds
    
    Usage:
        @throttle(1.0)
        def on_scroll():
            ...
    """
    def decorator(func: Callable) -> Callable:
        last_called: float = 0
        lock = threading.Lock()
        
        @wraps(func)
        def throttled(*args, **kwargs):
            nonlocal last_called
            
            with lock:
                now = time.time()
                if now - last_called >= wait:
                    last_called = now
                    return func(*args, **kwargs)
        
        return throttled
    return decorator


# ==================== Retry ====================

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Backoff multiplier
        exceptions: Exceptions to catch
    
    Usage:
        @retry(max_attempts=3, delay=0.5)
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


# ==================== File Helpers ====================

def download_file(
    data: bytes,
    filename: str,
    mime_type: str = "application/octet-stream",
    label: str = "Download",
) -> None:
    """
    Create a download button in Streamlit.
    
    Args:
        data: File data as bytes
        filename: Download filename
        mime_type: MIME type
        label: Button label
    """
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{label}</a>'
    st.markdown(href, unsafe_allow_html=True)


def download_json(
    data: Dict[str, Any],
    filename: str = "data.json",
    label: str = "Download JSON",
) -> None:
    """Download data as JSON file."""
    json_str = json.dumps(data, indent=2, default=str)
    download_file(json_str.encode(), filename, "application/json", label)


def download_csv(
    data: List[Dict[str, Any]],
    filename: str = "data.csv",
    label: str = "Download CSV",
) -> None:
    """Download data as CSV file."""
    import csv
    import io
    
    if not data:
        st.warning("No data to download")
        return
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    download_file(output.getvalue().encode(), filename, "text/csv", label)


def copy_to_clipboard(text: str, label: str = "Copy") -> None:
    """
    Create a copy-to-clipboard button in Streamlit.
    
    Args:
        text: Text to copy
        label: Button label
    """
    st.markdown(f"""
    <div style="display: inline-block;">
        <button onclick="navigator.clipboard.writeText(`{text}`)" 
                style="padding: 0.25rem 0.75rem; border-radius: 4px; border: 1px solid #ccc; 
                       background: #2d2d44; color: white; cursor: pointer;">
            📋 {label}
        </button>
    </div>
    """, unsafe_allow_html=True)


def get_file_extension(filename: str) -> str:
    """Get file extension with dot (e.g., '.txt')."""
    return Path(filename).suffix.lower()


def get_mime_type(filename: str) -> str:
    """Get MIME type from filename extension."""
    ext = get_file_extension(filename)
    
    mime_types = {
        ".txt": "text/plain",
        ".csv": "text/csv",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".pdf": "application/pdf",
        ".zip": "application/zip",
        ".mp4": "video/mp4",
        ".mp3": "audio/mpeg",
    }
    
    return mime_types.get(ext, "application/octet-stream")


# ==================== JWT Helpers ====================

def parse_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Parse JWT token without validation.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload or None
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        
        payload = parts[1]
        # Add padding if needed
        payload += "=" * ((4 - len(payload) % 4) % 4)
        decoded = base64.urlsafe_b64decode(payload)
        
        return json.loads(decoded)
    except Exception:
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if JWT token is expired.
    
    Args:
        token: JWT token string
    
    Returns:
        True if expired or invalid
    """
    payload = parse_jwt(token)
    
    if not payload or "exp" not in payload:
        return True
    
    exp_timestamp = payload["exp"]
    return datetime.utcnow().timestamp() > exp_timestamp


# ==================== Array Helpers ====================

def chunk_array(arr: List[T], chunk_size: int) -> Iterator[List[T]]:
    """
    Split array into chunks.
    
    Args:
        arr: Array to chunk
        chunk_size: Size of each chunk
    
    Yields:
        Chunks of the array
    """
    for i in range(0, len(arr), chunk_size):
        yield arr[i:i + chunk_size]


def group_by(arr: List[Dict[str, Any]], key: str) -> Dict[Any, List[Dict[str, Any]]]:
    """
    Group array of dictionaries by key.
    
    Args:
        arr: Array of dictionaries
        key: Key to group by
    
    Returns:
        Grouped dictionary
    """
    result: Dict[Any, List[Dict[str, Any]]] = {}
    
    for item in arr:
        value = item.get(key)
        if value not in result:
            result[value] = []
        result[value].append(item)
    
    return result


# ==================== Object Helpers ====================

def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
    
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def safe_get(obj: Any, path: str, default: Any = None) -> Any:
    """
    Safely get nested value using dot notation.
    
    Args:
        obj: Object to traverse
        path: Dot-separated path (e.g., "user.profile.name")
        default: Default value if not found
    
    Returns:
        Value at path or default
    """
    if obj is None:
        return default
    
    parts = path.split(".")
    current = obj
    
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return default
        
        if current is None:
            return default
    
    return current


# ==================== Async Helpers ====================

def run_async(coro):
    """
    Run async function in Streamlit.
    
    Args:
        coro: Coroutine to run
    
    Returns:
        Result of coroutine
    """
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create new loop in thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ==================== Streamlit Helpers ====================

def get_query_params() -> Dict[str, Any]:
    """Get URL query parameters."""
    return st.query_params.to_dict()


def set_query_params(params: Dict[str, Any]) -> None:
    """Set URL query parameters."""
    st.query_params.update(params)


def clear_query_params() -> None:
    """Clear all query parameters."""
    st.query_params.clear()


def scroll_to_top() -> None:
    """Scroll to top of page."""
    st.markdown("""
    <script>
        window.scrollTo(0, 0);
    </script>
    """, unsafe_allow_html=True)


def scroll_to_bottom() -> None:
    """Scroll to bottom of page."""
    st.markdown("""
    <script>
        window.scrollTo(0, document.body.scrollHeight);
    </script>
    """, unsafe_allow_html=True)


def inject_custom_css(css: str) -> None:
    """Inject custom CSS."""
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def inject_javascript(js: str) -> None:
    """Inject JavaScript."""
    st.markdown(f"<script>{js}</script>", unsafe_allow_html=True)


# ==================== Color Helpers ====================

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color."""
    return f"#{r:02x}{g:02x}{b:02x}"


def lighten_color(hex_color: str, factor: float = 0.3) -> str:
    """Lighten a hex color."""
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)


def darken_color(hex_color: str, factor: float = 0.3) -> str:
    """Darken a hex color."""
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return rgb_to_hex(r, g, b)


# ==================== String Helpers ====================

def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
    
    Returns:
        Slug string
    """
    import re
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces with hyphens
    text = re.sub(r"\s+", "-", text)
    
    # Remove non-alphanumeric characters
    text = re.sub(r"[^a-z0-9-]", "", text)
    
    # Remove consecutive hyphens
    text = re.sub(r"-+", "-", text)
    
    # Remove leading/trailing hyphens
    text = text.strip("-")
    
    return text


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text to extract from
    
    Returns:
        List of hashtags (without #)
    """
    import re
    pattern = r"#(\w+)"
    return re.findall(pattern, text)


def highlight_text(text: str, query: str, color: str = "#00d2ff") -> str:
    """
    Highlight search query in text.
    
    Args:
        text: Text to highlight
        query: Query to highlight
        color: Highlight color
    
    Returns:
        HTML with highlighted text
    """
    if not query or not text:
        return text
    
    import re
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    highlighted = pattern.sub(f'<span style="background-color: {color}; padding: 0 2px;">\\g<0></span>', text)
    return highlighted


# ==================== Math Helpers ====================

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))


def lerp(start: float, end: float, t: float) -> float:
    """Linear interpolation."""
    return start + (end - start) * clamp(t, 0.0, 1.0)


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Normalize value to 0-1 range."""
    if max_val == min_val:
        return 0.0
    return clamp((value - min_val) / (max_val - min_val), 0.0, 1.0)


# ==================== Time Helpers ====================

def time_ago(dt: datetime) -> str:
    """
    Get relative time string (e.g., "2 hours ago").
    
    Args:
        dt: Datetime to compare
    
    Returns:
        Relative time string
    """
    from src.presentation.web.utils.formatters import _format_relative_time
    return _format_relative_time(dt)


def is_today(dt: datetime) -> bool:
    """Check if datetime is today."""
    return dt.date() == datetime.utcnow().date()


def is_yesterday(dt: datetime) -> bool:
    """Check if datetime is yesterday."""
    yesterday = datetime.utcnow() - __import__("datetime").timedelta(days=1)
    return dt.date() == yesterday.date()