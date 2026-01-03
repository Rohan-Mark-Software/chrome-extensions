from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
import requests
from bs4 import BeautifulSoup
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
CORS(app)

app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'  
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  
cache = Cache(app)

try:
    with app.app_context():
        cache.set('startup_test', 'working', timeout=10)
        test_value = cache.get('startup_test')
        if test_value == 'working':
            print("✅ Redis cache connection successful!")
        else:
            print("❌ Redis cache test failed - value mismatch")
except Exception as e:
    print(f"❌ Redis cache initialization error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# HELPER FUNCTIONS (shared by all variants)
# ============================================================================

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
        score += text.count(term) * 2
    
    title_lower = result.get('title', '').lower()
    for term in query_terms:
        if term in title_lower:
            score += 5
    
    return score

def merge_and_rank_results(all_results, query, max_results=10):
    """Merge results from multiple sources and rank by relevance"""
    seen_urls = set()
    unique_results = []
    
    for result in all_results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            result['relevance_score'] = calculate_relevance_score(result, query)
            unique_results.append(result)
    
    ranked_results = sorted(unique_results, key=lambda x: x['relevance_score'], reverse=True)
    return ranked_results[:max_results]

def format_response(query, ranked_results):
    """Format search results into response"""
    context = '\n\n'.join([
        f"{r['title']}\n{r['snippet']}"
        for r in ranked_results
    ])
    
    return {
        'success': True,
        'query': query,
        'data': ranked_results,
        'context': context,
        'count': len(ranked_results)
    }

# ============================================================================
# VERSION 1: WITHOUT THREADS (Sequential)
# ============================================================================

@app.route('/search/sequential', methods=['GET'])
def search_sequential():
    """Sequential search without threading"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter "q" is required'}), 400

    engines = request.args.get('engines', 'duckduckgo,bing').split(',')
    max_results = min(int(request.args.get('max_results', 10)), 50)
    
    try:
        all_results = []
        
        # Sequential execution - one after another
        if 'duckduckgo' in engines:
            ddg_results = search_duckduckgo(query, max_results)
            all_results.extend(ddg_results)
        
        if 'bing' in engines:
            bing_results = search_bing(query, max_results)
            all_results.extend(bing_results)
        
        if not all_results:
            return jsonify({
                'success': True,
                'query': query,
                'data': [],
                'context': "",
                'message': 'No results found'
            })
        
        ranked_results = merge_and_rank_results(all_results, query, max_results)
        return jsonify(format_response(query, ranked_results)), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# VERSION 2: WITH THREADS (Parallel)
# ============================================================================

@app.route('/search/parallel', methods=['GET'])
def search_parallel():
    """Parallel search with threading"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter "q" is required'}), 400

    engines = request.args.get('engines', 'duckduckgo,bing').split(',')
    max_results = min(int(request.args.get('max_results', 10)), 50)
    
    try:
        all_results = []
        
        # Parallel execution using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_engine = {}
            
            if 'duckduckgo' in engines:
                future = executor.submit(search_duckduckgo, query, max_results)
                future_to_engine[future] = 'duckduckgo'
            
            if 'bing' in engines:
                future = executor.submit(search_bing, query, max_results)
                future_to_engine[future] = 'bing'
            
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"{engine_name} search failed: {str(e)}")
        
        if not all_results:
            return jsonify({
                'success': True,
                'query': query,
                'data': [],
                'context': "",
                'message': 'No results found'
            })
        
        ranked_results = merge_and_rank_results(all_results, query, max_results)
        return jsonify(format_response(query, ranked_results)), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# VERSION 3: WITH THREADS AND CACHE
# ============================================================================

def get_cache_key(query, engines, max_results):
    """Generate cache key from query parameters"""
    key_string = f"{query}_{engines}_{max_results}"
    return hashlib.md5(key_string.encode()).hexdigest()

@app.route('/search', methods=['GET'])
def search():
    """Parallel search with threading and caching"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter "q" is required'}), 400

    engines = request.args.get('engines', 'duckduckgo,bing').split(',')
    max_results = min(int(request.args.get('max_results', 10)), 50)
    
    cache_key = f"search:{query}:{','.join(sorted(engines))}:{max_results}"
    
    # Try to get from cache first
    cached_response = cache.get(cache_key)
    if cached_response:
        print(f"✅ Cache HIT for: {query}")
        cached_response['cached'] = True
        return jsonify(cached_response), 200
    
    print(f"❌ Cache MISS for: {query}")
    
    try:
        all_results = []
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_engine = {}
            
            if 'duckduckgo' in engines:
                future = executor.submit(search_duckduckgo, query, max_results)
                future_to_engine[future] = 'duckduckgo'
            
            if 'bing' in engines:
                future = executor.submit(search_bing, query, max_results)
                future_to_engine[future] = 'bing'
            
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"{engine_name} search failed: {str(e)}")
        
        if not all_results:
            response = {
                'success': True,
                'query': query,
                'data': [],
                'context': "",
                'message': 'No results found',
                'cached': False
            }
            return jsonify(response)
        
        ranked_results = merge_and_rank_results(all_results, query, max_results)
        response = format_response(query, ranked_results)
        response['cached'] = False
        
        # Store in cache
        cache.set(cache_key, response, timeout=300)
        print(f"💾 Cached result for: {query}")
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached search results"""
    cache.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'})

@app.route('/cache/stats', methods=['GET'])
def cache_stats():
    """Get cache statistics"""
    # Note: SimpleCache doesn't provide detailed stats
    return jsonify({
        'cache_type': app.config['CACHE_TYPE'],
        'timeout': app.config['CACHE_DEFAULT_TIMEOUT']
    })

@app.route('/cache/test', methods=['GET'])
def test_cache():
    """Test cache functionality and show actual backend"""
    try:
        # Set a test value
        cache.set('test_key_123', 'test_value_456', timeout=60)
        
        # Try to get it back
        result = cache.get('test_key_123')
        
        return jsonify({
            'cache_backend_class': str(type(cache.cache).__name__),
            'cache_config': app.config['CACHE_TYPE'],
            'test_set': True,
            'test_get': result,
            'working': result == 'test_value_456',
            'redis_host': app.config.get('CACHE_REDIS_HOST'),
            'redis_port': app.config.get('CACHE_REDIS_PORT')
        })
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'cache_backend_class': str(type(cache.cache).__name__)
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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, debug=False)