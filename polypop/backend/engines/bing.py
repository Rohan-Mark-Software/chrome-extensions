"""
Bing search engine implementation
"""
import requests
from bs4 import BeautifulSoup
from typing import List
from engines.base import BaseSearchEngine
from models.search_result import SearchResult


class BingEngine(BaseSearchEngine):
    """Bing search engine"""
    
    @property
    def name(self) -> str:
        return 'bing'
    
    def search(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search Bing and extract results
        
        Args:
            query: Search query
            num_results: Max results to return
            
        Returns:
            List of SearchResult objects
        """
        try:
            response = requests.get(
                'https://www.bing.com/search',
                params={'q': query},
                headers=self._get_headers(),
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for result in soup.find_all('li', class_='b_algo')[:num_results]:
                title_elem = result.find('h2')
                snippet_elem = result.find('p')
                link_elem = result.find('a')
                
                if title_elem and snippet_elem and link_elem:
                    results.append(SearchResult(
                        title=title_elem.get_text(strip=True),
                        snippet=snippet_elem.get_text(strip=True),
                        url=link_elem.get('href', ''),
                        source=self.name
                    ))
            
            return results
            
        except Exception as e:
            print(f"Bing search error: {str(e)}")
            return []