"""
Data models for search results
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SearchResult:
    """Single search result"""
    title: str
    snippet: str
    url: str
    source: str
    relevance_score: int = 0
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'title': self.title,
            'snippet': self.snippet,
            'url': self.url,
            'source': self.source,
            'relevance_score': self.relevance_score
        }


@dataclass
class SearchResponse:
    """Complete search response"""
    success: bool
    query: str
    data: List[dict]
    context: str
    count: int
    cached: bool = False
    message: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary"""
        response = {
            'success': self.success,
            'query': self.query,
            'data': self.data,
            'context': self.context,
            'count': self.count,
            'cached': self.cached
        }
        if self.message:
            response['message'] = self.message
        return response