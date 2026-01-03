"""
Utilities for formatting API responses
"""
from typing import List
from models.search_result import SearchResult, SearchResponse


def format_search_response(
    query: str,
    results: List[SearchResult],
    cached: bool = False
) -> SearchResponse:
    """
    Format search results into standardized response
    
    Args:
        query: Original search query
        results: List of SearchResult objects
        cached: Whether results came from cache
        
    Returns:
        SearchResponse object
    """
    # Convert results to dicts
    data = [r.to_dict() for r in results]
    
    # Create context string
    context = '\n\n'.join([
        f"{r.title}\n{r.snippet}"
        for r in results
    ])
    
    return SearchResponse(
        success=True,
        query=query,
        data=data,
        context=context,
        count=len(results),
        cached=cached
    )


def format_empty_response(query: str) -> SearchResponse:
    """
    Format empty search response
    
    Args:
        query: Original search query
        
    Returns:
        SearchResponse object with no results
    """
    return SearchResponse(
        success=True,
        query=query,
        data=[],
        context="",
        count=0,
        cached=False,
        message='No results found'
    )


def format_error_response(error: str) -> dict:
    """
    Format error response
    
    Args:
        error: Error message
        
    Returns:
        Error response dictionary
    """
    return {
        'success': False,
        'error': error
    }