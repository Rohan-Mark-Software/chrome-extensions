"""
Base search engine interface
"""
from abc import ABC, abstractmethod
from typing import List
from models.search_result import SearchResult


class BaseSearchEngine(ABC):
    """Abstract base class for search engines"""
    
    def __init__(self, timeout: int = 10, user_agent: str = None):
        self.timeout = timeout
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    
    @abstractmethod
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Execute search query
        
        Args:
            query: Search query string
            num_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the engine name"""
        pass
    
    def _get_headers(self) -> dict:
        """Get common request headers"""
        return {
            'User-Agent': self.user_agent
        }