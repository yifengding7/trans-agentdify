"""Cache management utilities for models and processed data."""

import os
import hashlib
import pickle
import json
from pathlib import Path
from typing import Any, Optional, Dict
from loguru import logger


class CacheManager:
    """Manages caching for models and processing results."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize cache manager.
        
        Args:
            cache_dir: Cache directory path. If None, uses default.
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.video_subtitle_cache")
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Cache manager initialized: {self.cache_dir}")
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        
        try:
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    value = pickle.load(f)
                logger.debug(f"Cache hit: {key}")
                return value
        except Exception as e:
            logger.warning(f"Failed to load cache {key}: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return default
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            logger.debug(f"Cached: {key}")
        except Exception as e:
            logger.warning(f"Failed to cache {key}: {e}")
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        return cache_file.exists()
    
    def delete(self, key: str) -> None:
        """Delete key from cache.
        
        Args:
            key: Cache key to delete
        """
        cache_file = self.cache_dir / f"{key}.pkl"
        
        try:
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Deleted cache: {key}")
        except Exception as e:
            logger.warning(f"Failed to delete cache {key}: {e}")
    
    def clear(self) -> None:
        """Clear all cache files."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            logger.info("Cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information.
        
        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_dir": str(self.cache_dir),
            "num_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / 1024 / 1024,
        }


# Global cache instance
_default_cache = None


def get_default_cache() -> CacheManager:
    """Get the default cache manager instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = CacheManager()
    return _default_cache


def cache_result(cache_key_func=None):
    """Decorator to cache function results.
    
    Args:
        cache_key_func: Function to generate cache key from args/kwargs
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_default_cache()
            
            # Generate cache key
            if cache_key_func:
                key = cache_key_func(*args, **kwargs)
            else:
                key = cache._get_cache_key(func.__name__, *args, **kwargs)
            
            # Check cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            
            return result
        
        return wrapper
    return decorator 