from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_core.prompts import ChatPromptTemplate
from urllib.parse import urlparse, parse_qs
import requests
import json


llm = ChatOllama(model="gpt-oss:120b-cloud", base_url="http://localhost:11434")

wrapper = DuckDuckGoSearchAPIWrapper(
    region="wt-wt",           
    safesearch="off",   
    time="d",                 
    max_results=30,           
    source="text",            
    backend="auto"            
)

search = DuckDuckGoSearchResults(
    api_wrapper=wrapper,
    num_results=30            
)


def extract_polymarket_slug(bet_url):
    """Extract slug from Polymarket URL"""
    parsed = urlparse(bet_url)
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) >= 2:
        return path_parts[1]  # Return the slug
    return None


def get_polymarket_event_data(slug):
    """
    Fetch event data from Polymarket API using the slug
    
    Correct API Endpoint: https://gamma-api.polymarket.com/events/slug/{slug}
    """
    
    base_url = "https://gamma-api.polymarket.com"
    # CORRECTED: Use /events/slug/{slug} format
    endpoint = f"{base_url}/events/slug/{slug}"
    
    try:
        print(f"🌐 Fetching event data from Polymarket API...")
        print(f"📡 Endpoint: {endpoint}\n")
        response = requests.get(endpoint)
        response.raise_for_status()
        
        event_data = response.json()
        return event_data
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching Polymarket data: {e}")
        return None


def format_polymarket_data(event_data):
    """Format Polymarket event data into readable text"""
    
    if not event_data:
        return "No event data available"
    
    formatted = f"""
📊 POLYMARKET EVENT DATA
{'='*60}

📋 Event: {event_data.get('title', 'N/A')}
📝 Description: {event_data.get('description', 'N/A')}
🔗 Event ID: {event_data.get('id', 'N/A')}
🏷️  Slug: {event_data.get('slug', 'N/A')}

🎯 MARKETS & CURRENT ODDS:
"""
    
    markets = event_data.get('markets', [])
    
    if not markets:
        formatted += "\n⚠️  No markets found for this event\n"
    
    for i, market in enumerate(markets, 1):
        formatted += f"\n{'─'*60}\n"
        formatted += f"Market {i}: {market.get('question', 'N/A')}\n"
        formatted += f"Market ID: {market.get('id', 'N/A')}\n"
        formatted += f"Condition ID: {market.get('conditionId', 'N/A')}\n"
        
        # Get outcome tokens
        outcome_prices = market.get('outcomePrices', [])
        tokens = market.get('tokens', [])
        outcomes = market.get('outcomes', [])
        
        formatted += f"\n💰 OUTCOMES & ODDS:\n"
        
        for j, outcome in enumerate(outcomes):
            price = outcome_prices[j] if j < len(outcome_prices) else 'N/A'
            
            # Convert price to percentage (Polymarket prices are strings like "0.45")
            if price != 'N/A':
                try:
                    percentage = f"{float(price) * 100:.2f}%"
                except:
                    percentage = price
            else:
                percentage = "N/A"
            
            formatted += f"  {j+1}. {outcome}: {percentage} (implied probability)\n"
        
        # Volume and liquidity
        volume = market.get('volume', 'N/A')
        volume24hr = market.get('volume24hr', 'N/A')
        liquidity = market.get('liquidity', 'N/A')
        
        formatted += f"\n📈 MARKET STATS:\n"
        if isinstance(volume, (int, float)):
            formatted += f"  • Total Volume: ${volume:,.2f}\n"
        else:
            formatted += f"  • Total Volume: {volume}\n"
            
        if isinstance(volume24hr, (int, float)):
            formatted += f"  • 24h Volume: ${volume24hr:,.2f}\n"
        else:
            formatted += f"  • 24h Volume: {volume24hr}\n"
            
        if isinstance(liquidity, (int, float)):
            formatted += f"  • Liquidity: ${liquidity:,.2f}\n"
        else:
            formatted += f"  • Liquidity: {liquidity}\n"
        
        # Trading status
        active = market.get('active', False)
        closed = market.get('closed', False)
        formatted += f"  • Status: {'🟢 Active' if active and not closed else '🔴 Closed'}\n"
    
    # Event metadata
    formatted += f"\n{'='*60}\n"
    formatted += f"📅 EVENT INFO:\n"
    formatted += f"  • Start Date: {event_data.get('startDate', 'N/A')}\n"
    formatted += f"  • End Date: {event_data.get('endDate', 'N/A')}\n"
    formatted += f"  • Close Time: {event_data.get('end_date_iso', event_data.get('endDate', 'N/A'))}\n"
    
    tags = event_data.get('tags', [])
    if tags:
        tag_names = [tag.get('label', tag.get('slug', 'Unknown')) if isinstance(tag, dict) else str(tag) for tag in tags]
        formatted += f"  • Tags: {', '.join(tag_names)}\n"
    
    formatted += f"  • Active: {'✅ Yes' if event_data.get('active', False) else '❌ No'}\n"
    formatted += f"  • Closed: {'✅ Yes' if event_data.get('closed', False) else '❌ No'}\n"
    
    return formatted


def analyze_polymarket_bet_with_api(bet_url):
    """
    Comprehensive Polymarket bet analysis using official API + web search
    """
    
    # Extract slug from URL
    slug = extract_polymarket_slug(bet_url)
    
    if not slug:
        return "❌ Could not extract event slug from URL"
    
    print(f"🎯 ANALYZING POLYMARKET BET")
    print(f"{'='*60}")
    print(f"🔗 URL: {bet_url}")
    print(f"📌 Slug: {slug}")
    print(f"{'='*60}\n")
    
    # Get official Polymarket data
    event_data = get_polymarket_event_data(slug)
    
    if event_data:
        formatted_event_data = format_polymarket_data(event_data)
        print(formatted_event_data)
        print("\n")
    else:
        formatted_event_data = "Could not fetch event data from Polymarket API"
    
    # Get event title for better searches
    event_title = event_data.get('title', slug.replace('-', ' ')) if event_data else slug.replace('-', ' ')
    
    # Web search for additional context
    print("🔍 Searching for additional context and news...\n")
    queries = [
        f"{event_title} latest news",
        f"{event_title} predictions analysis",
        f"Polymarket {event_title} odds"
    ]
    
    all_search_results = []
    for i, query in enumerate(queries, 1):
        print(f"Search {i}/{len(queries)}: {query}")
        try:
            results = search.run(query)
            all_search_results.append(f"=== Search {i}: {query} ===\n{results}\n")
        except Exception as e:
            print(f"⚠️  Search failed: {e}")
    
    combined_search_context = "\n".join(all_search_results)
    
    # Combine Polymarket data + web search results
    full_context = f"""
{formatted_event_data}

{'='*60}
ADDITIONAL WEB RESEARCH:
{'='*60}
{combined_search_context}
"""
    
    template = """You are a professional Polymarket betting analyst with access to real-time market data.

🎯 POLYMARKET BET: {bet_url}

📊 OFFICIAL MARKET DATA + RESEARCH:
{context}

Provide a data-driven betting analysis:

**📈 CURRENT MARKET STATE**
- Current odds for each outcome (from API data)
- Volume and liquidity analysis
- Market sentiment and movement

**🎲 RECOMMENDED BET** ⭐
- Outcome: [Specific option with current odds]
- Why This Pick: [Based on odds vs true probability]
- Expected Value: [Calculate if odds are favorable]
- Key Supporting Factors: [2-3 main reasons]

**📊 MARKET EFFICIENCY ANALYSIS**
- Are current odds accurate?
- Identify any mispriced outcomes
- Compare market odds vs real-world probability

**⚡ ALTERNATIVE PLAYS**
- Second best option with rationale
- Contrarian bet (if viable underdog exists)

**⚠️ RISK FACTORS**
- What could invalidate this bet
- Key uncertainties
- Time-sensitive factors

**💰 BETTING STRATEGY**
- Position Size: Conservative/Moderate/Aggressive
- Entry timing recommendation
- Exit strategy if applicable

**🎯 CONFIDENCE: [X/10]**
- Explain your confidence level based on data quality and market analysis

Be analytical, data-driven, and focus on VALUE. Compare market odds to true probabilities.
"""
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm
    
    response = chain.invoke({
        "bet_url": bet_url,
        "context": full_context
    })
    
    return response.content


# Usage
result = analyze_polymarket_bet_with_api(
    "https://polymarket.com/event/of-views-of-next-mrbeast-video-on-day-1-486"
)

print("\n" + "="*60)
print("🎯 FINAL BETTING RECOMMENDATION")
print("="*60 + "\n")
print(result)