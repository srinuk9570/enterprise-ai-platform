"""
Cache manager for Streamlit application.
Provides TTL-based caching and resource caching.
"""
import streamlit as st
from typing import Optional, Any, Dict, List, Callable
from datetime import datetime, timedelta
import hashlib
import json
import threading
import time
import logging

logger = logging.getLogger(__name__)


class CacheEntry:
    """Cache entry with TTL support."""
    
    def __init__(self, value: Any, ttl_seconds: Optional[int] = None):
        self.value = value
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        
        elapsed = (datetime.utcnow() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds
    
    def access(self):
        """Record access to this entry."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


class CacheManager:
    """
    Cache manager with TTL support and multiple storage backends.
    Supports session cache, memory cache, and persistent cache.
    """
    
    # Cache storage
    _memory_cache: Dict[str, CacheEntry] = {}
    _persistent_cache: Dict[str, CacheEntry] = {}
    _lock = threading.RLock()
    
    # Default TTLs (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    LONG_TTL = 3600  # 1 hour
    SHORT_TTL = 60  # 1 minute
    
    # Cleanup settings
    _last_cleanup = datetime.utcnow()
    CLEANUP_INTERVAL = 300  # 5 minutes
    
    @classmethod
    def _generate_key(cls, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = {
            "args": args,
            "kwargs": kwargs,
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    @classmethod
    def _cleanup_expired(cls):
        """Remove expired entries from all caches."""
        now = datetime.utcnow()
        
        if (now - cls._last_cleanup).total_seconds() < cls.CLEANUP_INTERVAL:
            return
        
        with cls._lock:
            # Clean memory cache
            expired_keys = [
                key for key, entry in cls._memory_cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del cls._memory_cache[key]
            
            # Clean persistent cache
            expired_keys = [
                key for key, entry in cls._persistent_cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del cls._persistent_cache[key]
            
            cls._last_cleanup = now
            
            if expired_keys:
                logger.debug(f"Cleaned {len(expired_keys)} expired cache entries")
    
    # ==================== Memory Cache ====================
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get a value from memory cache."""
        cls._cleanup_expired()
        
        with cls._lock:
            entry = cls._memory_cache.get(key)
            
            if entry and not entry.is_expired():
                entry.access()
                return entry.value
            
            return default
    
    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set a value in memory cache."""
        ttl = ttl_seconds if ttl_seconds is not None else cls.DEFAULT_TTL
        
        with cls._lock:
            cls._memory_cache[key] = CacheEntry(value, ttl)
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """Delete a value from memory cache."""
        with cls._lock:
            if key in cls._memory_cache:
                del cls._memory_cache[key]
                return True
            return False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all memory cache."""
        with cls._lock:
            cls._memory_cache.clear()
            logger.info("Memory cache cleared")
    
    @classmethod
    def has(cls, key: str) -> bool:
        """Check if key exists and is not expired."""
        cls._cleanup_expired()
        
        with cls._lock:
            entry = cls._memory_cache.get(key)
            return entry is not None and not entry.is_expired()
    
    # ==================== Persistent Cache (Session State) ====================
    
    @classmethod
    def get_persistent(cls, key: str, default: Any = None) -> Any:
        """Get a value from persistent cache (Streamlit session state)."""
        cache_key = f"cache_{key}"
        
        if cache_key in st.session_state:
            entry_data = st.session_state[cache_key]
            created_at = datetime.fromisoformat(entry_data["created_at"])
            ttl = entry_data.get("ttl")
            
            if ttl is None or (datetime.utcnow() - created_at).total_seconds() < ttl:
                return entry_data["value"]
            else:
                del st.session_state[cache_key]
        
        return default
    
    @classmethod
    def set_persistent(cls, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set a value in persistent cache."""
        cache_key = f"cache_{key}"
        
        st.session_state[cache_key] = {
            "value": value,
            "created_at": datetime.utcnow().isoformat(),
            "ttl": ttl_seconds,
        }
    
    @classmethod
    def delete_persistent(cls, key: str) -> bool:
        """Delete a value from persistent cache."""
        cache_key = f"cache_{key}"
        
        if cache_key in st.session_state:
            del st.session_state[cache_key]
            return True
        return False
    
    # ==================== Decorators ====================
    
    @classmethod
    def cached(cls, ttl_seconds: Optional[int] = None):
        """
        Decorator for caching function results.
        
        Usage:
            @CacheManager.cached(ttl_seconds=300)
            def expensive_function(arg1, arg2):
                return result
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Generate cache key
                key = f"{func.__module__}.{func.__name__}:{cls._generate_key(*args, **kwargs)}"
                
                # Check cache
                cached = cls.get(key)
                if cached is not None:
                    return cached
                
                # Compute and cache
                result = func(*args, **kwargs)
                cls.set(key, result, ttl_seconds)
                
                return result
            
            return wrapper
        return decorator
    
    @classmethod
    def cached_persistent(cls, ttl_seconds: Optional[int] = None):
        """
        Decorator for caching in persistent storage.
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                key = f"{func.__module__}.{func.__name__}:{cls._generate_key(*args, **kwargs)}"
                
                cached = cls.get_persistent(key)
                if cached is not None:
                    return cached
                
                result = func(*args, **kwargs)
                cls.set_persistent(key, result, ttl_seconds)
                
                return result
            
            return wrapper
        return decorator
    
    @classmethod
    def cached_st(cls, ttl_seconds: Optional[int] = None):
        """
        Streamlit-specific caching using @st.cache_data.
        """
        def decorator(func: Callable) -> Callable:
            @st.cache_data(ttl=ttl_seconds if ttl_seconds else cls.DEFAULT_TTL)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    # ==================== Resource Caching ====================
    
    @classmethod
    def cache_resource(cls, key: str, loader: Callable[[], Any], ttl_seconds: Optional[int] = None) -> Any:
        """
        Cache a resource with lazy loading.
        
        Args:
            key: Cache key
            loader: Function to load the resource if not cached
            ttl_seconds: TTL in seconds
        
        Returns:
            Cached resource
        """
        cached = cls.get(key)
        if cached is not None:
            return cached
        
        resource = loader()
        cls.set(key, resource, ttl_seconds or cls.LONG_TTL)
        return resource
    
    @classmethod
    def invalidate_resource(cls, key: str) -> bool:
        """Invalidate a cached resource."""
        return cls.delete(key)
    
    # ==================== Statistics ====================
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics."""
        cls._cleanup_expired()
        
        with cls._lock:
            memory_entries = len(cls._memory_cache)
            memory_accesses = sum(e.access_count for e in cls._memory_cache.values())
            
        return {
            "memory_cache": {
                "entries": memory_entries,
                "total_accesses": memory_accesses,
            },
            "last_cleanup": cls._last_cleanup.isoformat(),
        }
    
    @classmethod
    def get_keys(cls) -> List[str]:
        """Get all cache keys."""
        cls._cleanup_expired()
        
        with cls._lock:
            return list(cls._memory_cache.keys())


class DataCache:
    """
    Specialized cache for data fetching with deduplication.
    """
    
    _pending_requests: Dict[str, Any] = {}
    _lock = threading.RLock()
    
    @classmethod
    def fetch(
        cls,
        key: str,
        fetcher: Callable[[], Any],
        ttl_seconds: int = 300,
        force_refresh: bool = False,
    ) -> Any:
        """
        Fetch data with caching and request deduplication.
        
        Args:
            key: Cache key
            fetcher: Function to fetch data
            ttl_seconds: Cache TTL
            force_refresh: Force refresh ignoring cache
        
        Returns:
            Fetched data
        """
        # Check cache
        if not force_refresh:
            cached = CacheManager.get(key)
            if cached is not None:
                return cached
        
        # Check for pending request (deduplication)
        with cls._lock:
            if key in cls._pending_requests:
                # Wait for pending request
                future = cls._pending_requests[key]
                return future
        
        # Fetch data
        try:
            data = fetcher()
            CacheManager.set(key, data, ttl_seconds)
            return data
        finally:
            with cls._lock:
                cls._pending_requests.pop(key, None)