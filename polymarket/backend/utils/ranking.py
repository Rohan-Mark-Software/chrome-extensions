"""
Utilities for ranking and scoring search results
"""
from typing import List
from models.search_result import SearchResult


def calculate_relevance_score(result: SearchResult, query: str) -> int:
    """
    Calculate relevance score based on query term frequency
    
    Args:
        result: SearchResult object
        query: Search query string
        
    Returns:
        Relevance score (higher is better)
    """
    query_terms = query.lower().split()
    text = f"{result.title} {result.snippet}".lower()
    
    score = 0
    
    # Score based on term frequency in title + snippet
    for term in query_terms:
        score += text.count(term) * 2
    
    # Bonus points for terms in title
    title_lower = result.title.lower()
    for term in query_terms:
        if term in title_lower:
            score += 5
    
    return score


def merge_and_rank_results(
    all_results: List[SearchResult],
    query: str,
    max_results: int = 10
) -> List[SearchResult]:
    """
    Merge results from multiple sources and rank by relevance
    
    Args:
        all_results: List of SearchResult objects from all engines
        query: Original search query
        max_results: Maximum number of results to return
        
    Returns:
        Ranked and deduplicated list of SearchResult objects
    """
    seen_urls = set()
    unique_results = []
    
    # Deduplicate by URL
    for result in all_results:
        if result.url and result.url not in seen_urls:
            seen_urls.add(result.url)
            result.relevance_score = calculate_relevance_score(result, query)
            unique_results.append(result)
    
    # Sort by relevance score (descending)
    ranked_results = sorted(
        unique_results,
        key=lambda x: x.relevance_score,
        reverse=True
    )
    
    return ranked_results[:max_results]