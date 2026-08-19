"""
HTTP request logging middleware and utilities.
"""
import logging
import time
import uuid
from typing import Optional, Callable, Dict, Any
from contextlib import contextmanager
import json

logger = logging.getLogger(__name__)


class RequestLogger:
    """
    Logger for HTTP requests with timing and context tracking.
    """
    
    def __init__(self, logger_name: str = "request"):
        self.logger = logging.getLogger(logger_name)
        self.include_body: bool = False
        self.max_body_length: int = 1000
        self.sensitive_headers = {"authorization", "cookie", "x-api-key"}
    
    @contextmanager
    def log_request(self, method: str, path: str, **context):
        """
        Context manager to log request start and end.
        
        Usage:
            with request_logger.log_request("POST", "/api/chat", user_id=user_id):
                response = handle_request()
        """
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()
        
        # Log request start
        self.logger.info(
            f"Request started: {method} {path}",
            extra={
                "extra_fields": {
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "event": "request.start",
                    **context,
                }
            }
        )
        
        try:
            yield request_id
        except Exception as e:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                f"Request failed: {method} {path} - {type(e).__name__}",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_ms": duration_ms,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "event": "request.error",
                        **context,
                    }
                },
                exc_info=True,
            )
            raise
        else:
            # Log request completion
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.info(
                f"Request completed: {method} {path} - {duration_ms:.2f}ms",
                extra={
                    "extra_fields": {
                        "request_id": request_id,
                        "method": method,
                        "path": path,
                        "duration_ms": duration_ms,
                        "event": "request.complete",
                        **context,
                    }
                }
            )
    
    def log_request_start(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        **context,
    ) -> str:
        """
        Log the start of a request.
        Returns request_id for tracking.
        """
        request_id = str(uuid.uuid4())
        
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "event": "request.start",
            **context,
        }
        
        if headers:
            log_data["headers"] = self._sanitize_headers(headers)
        
        if body and self.include_body:
            log_data["body"] = self._sanitize_body(body)
        
        self.logger.info(
            f"Request started: {method} {path}",
            extra={"extra_fields": log_data}
        )
        
        return request_id
    
    def log_request_end(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        response_size: Optional[int] = None,
        **context,
    ) -> None:
        """
        Log the completion of a request.
        """
        log_data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "response_size": response_size,
            "event": "request.complete",
            **context,
        }
        
        log_level = logging.INFO
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        
        self.logger.log(
            log_level,
            f"Request completed: {method} {path} - {status_code} - {duration_ms:.2f}ms",
            extra={"extra_fields": log_data}
        )
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove sensitive headers from logging."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        return sanitized
    
    def _sanitize_body(self, body: Any) -> Any:
        """Truncate and sanitize request body."""
        if isinstance(body, dict):
            sanitized = {}
            for key, value in body.items():
                if key.lower() in {"password", "token", "secret", "api_key"}:
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = value
            body_str = json.dumps(sanitized)
        else:
            body_str = str(body)
        
        if len(body_str) > self.max_body_length:
            return body_str[:self.max_body_length] + "... [truncated]"
        return body_str


class AccessLogMiddleware:
    """
    Middleware for logging HTTP access in Apache combined log format.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        self.logger = logging.getLogger("access")
        self.logger.propagate = False
        
        if log_file:
            handler = logging.FileHandler(log_file)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
    
    def log(
        self,
        remote_addr: str,
        method: str,
        path: str,
        status: int,
        response_size: int,
        referer: str = "-",
        user_agent: str = "-",
    ) -> None:
        """
        Log in Apache combined log format.
        Format: %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-agent}i"
        """
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S %z")
        request_line = f"{method} {path} HTTP/1.1"
        
        log_line = (
            f'{remote_addr} - - [{timestamp}] "{request_line}" {status} {response_size} '
            f'"{referer}" "{user_agent}"'
        )
        
        self.logger.info(log_line)