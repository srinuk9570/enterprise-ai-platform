"""
Structured logging factory with multiple handlers and formatters.
"""
import logging
import logging.handlers
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading

from src.shared.config import settings


class LoggerFactory:
    """
    Factory for creating configured loggers with structured logging support.
    """
    
    _instance: Optional["LoggerFactory"] = None
    _lock = threading.Lock()
    _loggers: Dict[str, logging.Logger] = {}
    
    def __new__(cls) -> "LoggerFactory":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        self.log_file_path = Path(settings.LOG_FILE_PATH)
        self.log_dir = self.log_file_path.parent
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        self._configure_root_logger()
        
        self._initialized = True
    
    def _configure_root_logger(self) -> None:
        """Configure the root logger with handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(self._get_console_formatter())
        root_logger.addHandler(console_handler)
        
        # File handler (all logs)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=10,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self._get_file_formatter())
        root_logger.addHandler(file_handler)
        
        # Error file handler (errors only)
        error_log_path = self.log_dir / "error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._get_file_formatter())
        root_logger.addHandler(error_handler)
        
        # JSON file handler for structured logging
        json_log_path = self.log_dir / "structured.log"
        json_handler = logging.handlers.RotatingFileHandler(
            filename=json_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(self._get_json_formatter())
        root_logger.addHandler(json_handler)
    
    def _get_console_formatter(self) -> logging.Formatter:
        """Get formatter for console output."""
        if settings.DEBUG:
            return logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
                datefmt='%H:%M:%S',
            )
        else:
            return logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
            )
    
    def _get_file_formatter(self) -> logging.Formatter:
        """Get formatter for file output."""
        return logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
    
    def _get_json_formatter(self) -> logging.Formatter:
        """Get JSON formatter for structured logging."""
        return JsonFormatter()
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name.
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.log_level)
        
        # Don't propagate to root logger if we have handlers
        logger.propagate = False
        
        # Add handlers if not already present
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(self._get_console_formatter())
            logger.addHandler(console_handler)
            
            # File handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=self.log_file_path,
                maxBytes=10 * 1024 * 1024,
                backupCount=10,
                encoding='utf-8',
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(self._get_file_formatter())
            logger.addHandler(file_handler)
        
        self._loggers[name] = logger
        return logger
    
    def get_structured_logger(self, name: str) -> 'StructuredLogger':
        """
        Get a structured logger that outputs JSON.
        """
        return StructuredLogger(name)
    
    def set_log_level(self, level: str) -> None:
        """
        Change the log level for all loggers.
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.log_level = log_level
        
        # Update root logger
        logging.getLogger().setLevel(log_level)
        
        # Update all cached loggers
        for logger in self._loggers.values():
            logger.setLevel(log_level)
    
    def add_file_handler(self, filepath: Path, level: int = logging.INFO) -> None:
        """
        Add an additional file handler to all loggers.
        """
        handler = logging.handlers.RotatingFileHandler(
            filename=filepath,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        handler.setLevel(level)
        handler.setFormatter(self._get_file_formatter())
        
        logging.getLogger().addHandler(handler)
        
        for logger in self._loggers.values():
            logger.addHandler(handler)
    
    def get_log_files(self) -> List[Path]:
        """
        Get list of all log files.
        """
        log_files = list(self.log_dir.glob("*.log"))
        log_files.extend(self.log_dir.glob("*.log.*"))
        return sorted(log_files, key=lambda p: p.stat().st_mtime, reverse=True)
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """
        Delete log files older than specified days.
        """
        import time
        
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for log_file in self.log_dir.glob("*.log.*"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
        
        return deleted_count


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add request context if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        return json.dumps(log_data, default=str)


class StructuredLogger:
    """
    Logger that outputs structured JSON logs.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.extra_fields = {}
    
    def with_fields(self, **kwargs) -> 'StructuredLogger':
        """
        Add extra fields to all subsequent log messages.
        """
        self.extra_fields.update(kwargs)
        return self
    
    def with_request_context(
        self,
        request_id: str,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> 'StructuredLogger':
        """
        Add request context to logs.
        """
        self.extra_fields.update({
            "request_id": request_id,
            "user_id": user_id,
            "correlation_id": correlation_id,
        })
        return self
    
    def _log(self, level: int, message: str, **kwargs) -> None:
        """Internal log method with extra fields."""
        extra = {"extra_fields": {**self.extra_fields, **kwargs}}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs) -> None:
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs) -> None:
        """Log an exception with traceback."""
        self._log(logging.ERROR, message, **kwargs, exc_info=True)
    
    def event(self, event_name: str, **kwargs) -> None:
        """
        Log a business event.
        """
        self._log(logging.INFO, event_name, event=event_name, **kwargs)
    
    def metric(self, metric_name: str, value: float, **kwargs) -> None:
        """
        Log a metric value.
        """
        self._log(logging.DEBUG, f"Metric: {metric_name}={value}", 
                  metric=metric_name, value=value, **kwargs)


class LoggerFactorySingleton:
    """
    Singleton accessor for LoggerFactory.
    """
    
    _factory: Optional[LoggerFactory] = None
    
    @classmethod
    def get_factory(cls) -> LoggerFactory:
        if cls._factory is None:
            cls._factory = LoggerFactory()
        return cls._factory
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        return cls.get_factory().get_logger(name)
    
    @classmethod
    def get_structured_logger(cls, name: str) -> StructuredLogger:
        return cls.get_factory().get_structured_logger(name)