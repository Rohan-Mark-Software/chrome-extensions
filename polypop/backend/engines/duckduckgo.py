"""
DuckDuckGo search engine implementation
"""
import requests
from bs4 import BeautifulSoup
from typing import List
from engines.base import BaseSearchEngine
from models.search_result import SearchResult


class DuckDuckGoEngine(BaseSearchEngine):
    """DuckDuckGo search engine"""
    
    @property
    def name(self) -> str:
        return 'duckduckgo'
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search DuckDuckGo and extract results
        
        Args:
            query: Search query
            num_results: Max results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            response = requests.get(
                'https://html.duckduckgo.com/html/',
                params={'q': query},
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result in soup.find_all('div', class_='result')[:num_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and snippet_elem:
                    results.append(SearchResult(
                        title=title_elem.get_text(strip=True),
                        snippet=snippet_elem.get_text(strip=True),
                        url=title_elem.get('href', ''),
                        source=self.name
                    ))
            
            return results
            
        except Exception as e:
            print(f"DuckDuckGo search error: {str(e)}")
            return []