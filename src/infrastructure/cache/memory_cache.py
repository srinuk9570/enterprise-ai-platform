"""
In-memory cache with TTL support.
"""
import time
import threading
from typing import Optional, Any, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class MemoryCache:
    """
    Simple in-memory cache with TTL support.
    """
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or time.time() < expiry:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        with self._lock:
            expiry = None if ttl is None else time.time() + ttl
            self._cache[key] = (value, expiry)
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def clear(self) -> None:
        """Clear all cache."""
        with self._lock:
            self._cache.clear()
    
    def clear_expired(self) -> int:
        """Clear expired entries."""
        now = time.time()
        expired = []
        
        with self._lock:
            for key, (_, expiry) in self._cache.items():
                if expiry is not None and now >= expiry:
                    expired.append(key)
            
            for key in expired:
                del self._cache[key]
        
        return len(expired)
    
    def size(self) -> int:
        """Get number of entries."""
        with self._lock:
            return len(self._cache)