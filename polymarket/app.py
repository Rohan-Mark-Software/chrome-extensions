from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)  

@app.route('/search', methods=['GET'])
def search_duckduckgo():
    query = request.args.get('q', '')
    
    try:
        # Scrape DuckDuckGo HTML
        response = requests.get(
            'https://html.duckduckgo.com/html/',
            params={'q': query},
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('a', class_='result__snippet')
        
        context = '\n\n'.join([
            result.get_text(strip=True)
            for result in results[:3]
        ])
        
        return jsonify({
            'success': True,
            'data': context or 'No results found'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)