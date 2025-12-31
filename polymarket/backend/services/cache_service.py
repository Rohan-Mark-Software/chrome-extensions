"""
Cache service for managing search result caching
"""
import hashlib
from typing import Optional
from flask_caching import Cache


class CacheService:
    """Service for handling cache operations"""
    
    def __init__(self, cache: Cache):
        self.cache = cache
    
    def get_cache_key(self, query: str, engines: list, max_results: int) -> str:
        """
        Generate cache key from search parameters
        
        Args:
            query: Search query
            engines: List of engine names
            max_results: Maximum results
            
        Returns:
            Cache key string
        """
        engines_str = ','.join(sorted(engines))
        return f"search:{query}:{engines_str}:{max_results}"
    
    def get(self, cache_key: str) -> Optional[dict]:
        """
        Get cached response
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached response dict or None
        """
        try:
            return self.cache.get(cache_key)
        except Exception as e:
            print(f"Cache get error: {str(e)}")
            return None
    
    def set(self, cache_key: str, response: dict, timeout: int = 300) -> bool:
        """
        Store response in cache
        
        Args:
            cache_key: Cache key
            response: Response to cache
            timeout: Cache timeout in seconds
            
        Returns:
            True if successful
        """
        try:
            self.cache.set(cache_key, response, timeout=timeout)
            return True
        except Exception as e:
            print(f"Cache set error: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cached data
        
        Returns:
            True if successful
        """
        try:
            self.cache.clear()
            return True
        except Exception as e:
            print(f"Cache clear error: {str(e)}")
            return False
    
    def test(self) -> dict:
        """
        Test cache functionality
        
        Returns:
            Test results dict
        """
        try:
            test_key = 'test_key_123'
            test_value = 'test_value_456'
            
            self.cache.set(test_key, test_value, timeout=60)
            result = self.cache.get(test_key)
            
            return {
                'cache_backend_class': str(type(self.cache.cache).__name__),
                'test_set': True,
                'test_get': result,
                'working': result == test_value
            }
        except Exception as e:
            return {
                'error': str(e),
                'cache_backend_class': str(type(self.cache.cache).__name__)
            }