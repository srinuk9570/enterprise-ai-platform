"""
Advanced log formatters with color support and custom formats.
"""
import logging
import re
from datetime import datetime
from typing import Optional


class ColorFormatter(logging.Formatter):
    """
    Formatter that adds colors to console output.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
    }
    
    # Format patterns
    FORMATS = {
        'DEBUG': '%(asctime)s | \033[36m%(levelname)-8s\033[0m | %(name)s | %(message)s',
        'INFO': '%(asctime)s | \033[32m%(levelname)-8s\033[0m | %(name)s | %(message)s',
        'WARNING': '%(asctime)s | \033[33m%(levelname)-8s\033[0m | %(name)s | %(message)s',
        'ERROR': '%(asctime)s | \033[31m%(levelname)-8s\033[0m | %(name)s:%(lineno)d | %(message)s',
        'CRITICAL': '%(asctime)s | \033[35m%(levelname)-8s\033[0m | %(name)s:%(lineno)d | %(message)s',
    }
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors
        self.datefmt = '%Y-%m-%d %H:%M:%S'
    
    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            log_fmt = self.FORMATS.get(record.levelname, self.FORMATS['INFO'])
            formatter = logging.Formatter(log_fmt, datefmt=self.datefmt)
        else:
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
                datefmt=self.datefmt,
            )
        
        return formatter.format(record)


class DetailedFormatter(logging.Formatter):
    """
    Detailed formatter with process, thread, and module information.
    """
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(levelname)-8s | PID:%(process)d | %(threadName)s | '
                '%(name)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )


class SyslogFormatter(logging.Formatter):
    """
    Formatter compatible with syslog format.
    """
    
    def __init__(self, app_name: str = "enterprise-ai-platform"):
        super().__init__()
        self.app_name = app_name
    
    def format(self, record: logging.LogRecord) -> str:
        # Syslog priority calculation
        priority = self._get_priority(record.levelno)
        
        # Format: <PRI>TIMESTAMP HOSTNAME APPNAME[PID]: MESSAGE
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        hostname = record.hostname if hasattr(record, 'hostname') else 'localhost'
        
        return f"<{priority}>{timestamp} {hostname} {self.app_name}[{record.process}]: {record.getMessage()}"
    
    def _get_priority(self, levelno: int) -> int:
        """Convert Python log level to syslog priority."""
        # Facility: user-level messages (1)
        facility = 1
        
        # Severity mapping
        if levelno >= logging.CRITICAL:
            severity = 2  # Critical
        elif levelno >= logging.ERROR:
            severity = 3  # Error
        elif levelno >= logging.WARNING:
            severity = 4  # Warning
        elif levelno >= logging.INFO:
            severity = 6  # Informational
        else:
            severity = 7  # Debug
        
        return facility * 8 + severity


class MaskingFormatter(logging.Formatter):
    """
    Formatter that masks sensitive information in log messages.
    """
    
    # Patterns to mask
    PATTERNS = [
        (r'(password[=:]\s*)(\S+)', r'\1********'),
        (r'(api_key[=:]\s*)(\S+)', r'\1********'),
        (r'(token[=:]\s*)(\S+)', r'\1********'),
        (r'(secret[=:]\s*)(\S+)', r'\1********'),
        (r'(Authorization:\s*Bearer\s+)(\S+)', r'\1********'),
        (r'(email[\s]*[=:][\s]*)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1***@***.***'),
        (r'(\d{3}-\d{2}-\d{4})', r'***-**-****'),  # SSN
        (r'(\d{16})', r'****-****-****-****'),      # Credit card
    ]
    
    def __init__(self, base_formatter: Optional[logging.Formatter] = None):
        super().__init__()
        self.base_formatter = base_formatter or logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        # Format the record first
        formatted = self.base_formatter.format(record)
        
        # Apply masking patterns
        for pattern, replacement in self.PATTERNS:
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)
        
        return formatted