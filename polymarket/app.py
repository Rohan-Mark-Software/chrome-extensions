from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import time
from functools import lru_cache
import hashlib

app = Flask(__name__)
CORS(app)

# Cache results for 5 minutes to reduce redundant requests
@lru_cache(maxsize=100)
def cached_search(query_hash, engine, timestamp):
    """Cache wrapper - timestamp ensures cache expires every 5 minutes"""
    pass

def get_cache_timestamp():
    """Get current 5-minute block timestamp"""
    return int(time.time() / 300)

def search_duckduckgo(query, num_results=5):
    """Search DuckDuckGo and extract results"""
    try:
        response = requests.get(
            'https://html.duckduckgo.com/html/',
            params={'q': query},
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.find_all('div', class_='result')[:num_results]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('a', class_='result__snippet')
            
            if title_elem and snippet_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True),
                    'url': title_elem.get('href', ''),
                    'source': 'duckduckgo'
                })
        
        return results
    except Exception as e:
        print(f"DuckDuckGo error: {str(e)}")
        return []

def search_bing(query, num_results=5):
    """Search Bing and extract results"""
    try:
        response = requests.get(
            f'https://www.bing.com/search',
            params={'q': query},
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
            timeout=10
        )
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for result in soup.find_all('li', class_='b_algo')[:num_results]:
            title_elem = result.find('h2')
            snippet_elem = result.find('p')
            link_elem = result.find('a')
            
            if title_elem and snippet_elem and link_elem:
                results.append({
                    'title': title_elem.get_text(strip=True),
                    'snippet': snippet_elem.get_text(strip=True),
                    'url': link_elem.get('href', ''),
                    'source': 'bing'
                })
        
        return results
    except Exception as e:
        print(f"Bing error: {str(e)}")
        return []

def calculate_relevance_score(result, query):
    """Calculate relevance score based on query term frequency"""
    query_terms = query.lower().split()
    text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
    
    score = 0
    for term in query_terms:
        score += text.count(term) * 2  # Weight matches
    
    # Bonus for title matches
    title_lower = result.get('title', '').lower()
    for term in query_terms:
        if term in title_lower:
            score += 5
    
    return score

def merge_and_rank_results(all_results, query, max_results=10):
    """Merge results from multiple sources and rank by relevance"""
    # Remove duplicates based on URL
    seen_urls = set()
    unique_results = []
    
    for result in all_results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            result['relevance_score'] = calculate_relevance_score(result, query)
            unique_results.append(result)
    
    # Sort by relevance score
    ranked_results = sorted(unique_results, key=lambda x: x['relevance_score'], reverse=True)
    
    return ranked_results[:max_results]

@app.route('/search', methods=['GET'])
def search():
    """Multi-engine search endpoint with ranking"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter "q" is required'}), 400

    engines = request.args.get('engines', 'duckduckgo,bing').split(',')
    max_results = min(int(request.args.get('max_results', 10)), 50)
    
    try:
        all_results = []
        
        if 'duckduckgo' in engines:
            all_results.extend(search_duckduckgo(query, num_results=max_results))
        
        if 'bing' in engines:
            all_results.extend(search_bing(query, num_results=max_results))
        
        if not all_results:
            return jsonify({
                'success': True,
                'query': query,
                'data': [],  
                'context': "", 
                'message': 'No results found'
            })
        
        ranked_results = merge_and_rank_results(all_results, query, max_results)

        context = '\n\n'.join([
            f"{r['title']}\n{r['snippet']}"
            for r in ranked_results
        ])

        return jsonify({
            'success': True,
            'query': query,
            'data': ranked_results,  
            'context': context,       
            'count': len(ranked_results)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time()
    })

@app.route('/engines', methods=['GET'])
def list_engines():
    """List available search engines"""
    return jsonify({
        'engines': ['duckduckgo', 'bing'],
        'default': 'duckduckgo,bing'
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)