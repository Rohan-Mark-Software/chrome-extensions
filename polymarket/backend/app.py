import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

from config import config
from services.search_service import SearchService
from services.cache_service import CacheService
from utils.formatters import format_error_response


def create_app(config_name: str = None):

    app = Flask(__name__)
    
    config_name = config_name or os.getenv('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])

    CORS(app)
    cache = Cache(app)
    
    # Test cache connection
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
    
    search_service = SearchService(app.config)
    cache_service = CacheService(cache)
    

    @app.route('/search/sequential', methods=['GET'])
    def search_sequential():
        """Sequential search without threading"""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(format_error_response('Query parameter "q" is required')), 400
        
        engines = request.args.get('engines', 'duckduckgo,bing').split(',')
        max_results = min(int(request.args.get('max_results', app.config['DEFAULT_MAX_RESULTS'])), 
                         app.config['MAX_RESULTS_LIMIT'])
        
        try:
            response = search_service.search_sequential(query, engines, max_results)
            return jsonify(response.to_dict()), 200
        except Exception as e:
            return jsonify(format_error_response(str(e))), 500
    
    @app.route('/search/parallel', methods=['GET'])
    def search_parallel():
        """Parallel search with threading (no cache)"""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(format_error_response('Query parameter "q" is required')), 400
        
        engines = request.args.get('engines', 'duckduckgo,bing').split(',')
        max_results = min(int(request.args.get('max_results', app.config['DEFAULT_MAX_RESULTS'])), 
                         app.config['MAX_RESULTS_LIMIT'])
        
        try:
            response = search_service.search_parallel(query, engines, max_results)
            return jsonify(response.to_dict()), 200
        except Exception as e:
            return jsonify(format_error_response(str(e))), 500
    
    @app.route('/search', methods=['GET'])
    def search():
        """Parallel search with threading and caching"""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify(format_error_response('Query parameter "q" is required')), 400
        
        engines = request.args.get('engines', 'duckduckgo,bing').split(',')
        max_results = min(int(request.args.get('max_results', app.config['DEFAULT_MAX_RESULTS'])), 
                         app.config['MAX_RESULTS_LIMIT'])
        
        # Try cache first
        cache_key = cache_service.get_cache_key(query, engines, max_results)
        cached_response = cache_service.get(cache_key)
        
        if cached_response:
            print(f"✅ Cache HIT for: {query}")
            cached_response['cached'] = True
            return jsonify(cached_response), 200
        
        print(f"❌ Cache MISS for: {query}")
        
        try:
            response = search_service.search_parallel(query, engines, max_results)
            response_dict = response.to_dict()
            
            # Store in cache
            cache_service.set(cache_key, response_dict, app.config['CACHE_DEFAULT_TIMEOUT'])
            print(f"💾 Cached result for: {query}")
            
            return jsonify(response_dict), 200
        except Exception as e:
            return jsonify(format_error_response(str(e))), 500
    
    @app.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """Clear all cached search results"""
        success = cache_service.clear()
        if success:
            return jsonify({'success': True, 'message': 'Cache cleared'})
        return jsonify(format_error_response('Failed to clear cache')), 500
    
    @app.route('/cache/stats', methods=['GET'])
    def cache_stats():
        """Get cache statistics"""
        return jsonify({
            'cache_type': app.config['CACHE_TYPE'],
            'timeout': app.config['CACHE_DEFAULT_TIMEOUT'],
            'redis_host': app.config.get('CACHE_REDIS_HOST'),
            'redis_port': app.config.get('CACHE_REDIS_PORT')
        })
    
    @app.route('/cache/test', methods=['GET'])
    def test_cache():
        """Test cache functionality"""
        result = cache_service.test()
        if 'error' in result:
            return jsonify(result), 500
        return jsonify(result)
    
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
        engines = search_service.get_available_engines()
        return jsonify({
            'engines': engines,
            'default': ','.join(engines)
        })
    
    return app

if __name__ == '__main__':
    app = create_app('development')
    app.run(host="0.0.0.0", port=5001, debug=False)