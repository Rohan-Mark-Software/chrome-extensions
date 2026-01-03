"""
Search service for orchestrating multi-engine searches
"""
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from engines.base import BaseSearchEngine
from engines.duckduckgo import DuckDuckGoEngine
from engines.bing import BingEngine
from models.search_result import SearchResult, SearchResponse
from utils.ranking import merge_and_rank_results
from utils.formatters import format_search_response, format_empty_response


class SearchService:
    """Service for managing search operations"""
    
    def __init__(self, config: dict):
        self.timeout = config.get('REQUEST_TIMEOUT', 10)
        self.user_agent = config.get('USER_AGENT')
        self.thread_pool_size = config.get('THREAD_POOL_SIZE', 2)
        
        # Initialize search engines
        self.engines: Dict[str, BaseSearchEngine] = {
            'duckduckgo': DuckDuckGoEngine(self.timeout, self.user_agent),
            'bing': BingEngine(self.timeout, self.user_agent)
        }
    
    def search_sequential(
        self,
        query: str,
        engine_names: List[str],
        max_results: int
    ) -> SearchResponse:
        """
        Execute search sequentially (one engine at a time)
        
        Args:
            query: Search query
            engine_names: List of engine names to use
            max_results: Maximum results to return
            
        Returns:
            SearchResponse object
        """
        all_results = []
        
        for engine_name in engine_names:
            engine = self.engines.get(engine_name)
            if engine:
                results = engine.search(query, max_results)
                all_results.extend(results)
        
        if not all_results:
            return format_empty_response(query)
        
        ranked_results = merge_and_rank_results(all_results, query, max_results)
        return format_search_response(query, ranked_results)
    
    def search_parallel(
        self,
        query: str,
        engine_names: List[str],
        max_results: int
    ) -> SearchResponse:
        """
        Execute search in parallel (multiple engines simultaneously)
        
        Args:
            query: Search query
            engine_names: List of engine names to use
            max_results: Maximum results to return
            
        Returns:
            SearchResponse object
        """
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.thread_pool_size) as executor:
            # Submit search tasks
            future_to_engine = {}
            for engine_name in engine_names:
                engine = self.engines.get(engine_name)
                if engine:
                    future = executor.submit(engine.search, query, max_results)
                    future_to_engine[future] = engine_name
            
            # Collect results as they complete
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"{engine_name} search failed: {str(e)}")
        
        if not all_results:
            return format_empty_response(query)
        
        ranked_results = merge_and_rank_results(all_results, query, max_results)
        return format_search_response(query, ranked_results)
    
    def get_available_engines(self) -> List[str]:
        """
        Get list of available engine names
        
        Returns:
            List of engine names
        """
        return list(self.engines.keys())