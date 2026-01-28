#!/usr/bin/env python3
"""
Market search and discovery
"""

import os
import sys
import json
import argparse
import requests
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime

GAMMA_API = "https://gamma-api.polymarket.com"


def get_session():
    """Create requests session with retry logic"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def search_markets(query, limit=10):
    """Search markets by query (client-side filtering since API doesn't support text search)"""
    session = get_session()
    # Fetch active events
    url = f"{GAMMA_API}/events"
    params = {
        "active": "true",
        "closed": "false",
        "limit": 200  # Fetch more to filter
    }
    try:
        r = session.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return []
        events = r.json()
    except requests.RequestException as e:
        print(f"Error searching markets: {e}", file=sys.stderr)
        return []
    
    query_lower = query.lower()
    query_terms = query_lower.split()
    
    # Filter events by title/question containing query terms
    matches = []
    for e in events:
        title = e.get("title", "").lower()
        # Check if all query terms are in the title
        if all(term in title for term in query_terms):
            # Convert event to market format
            markets = e.get("markets", [])
            if markets:
                for m in markets:
                    m["event_title"] = e.get("title")
                    m["event_slug"] = e.get("slug")
                    matches.append(m)
            else:
                # Use event itself as market
                matches.append(e)
    
    return matches[:limit]


def get_trending(limit=10):
    """Get trending/active markets"""
    session = get_session()
    url = f"{GAMMA_API}/markets"
    params = {
        "limit": limit,
        "active": "true",
        "order": "volume24hr",
        "ascending": "false"
    }
    try:
        r = session.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException as e:
        print(f"Error fetching trending: {e}", file=sys.stderr)
    return []


def get_by_category(category, limit=10):
    """Get markets by category (politics, crypto, sports, etc)"""
    session = get_session()
    # Map common categories to tags
    category_map = {
        "politics": "politics",
        "crypto": "crypto",
        "sports": "sports",
        "entertainment": "entertainment",
        "science": "science",
        "business": "business",
        "finance": "finance"
    }
    tag = category_map.get(category.lower(), category)
    
    url = f"{GAMMA_API}/markets"
    params = {
        "tag": tag,
        "limit": limit,
        "active": "true",
        "order": "volume24hr",
        "ascending": "false"
    }
    try:
        r = session.get(url, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException as e:
        print(f"Error fetching category: {e}", file=sys.stderr)
    return []


def get_market_detail(market_id):
    """Get detailed market info including order book"""
    session = get_session()
    
    # Try events endpoint by slug first
    url = f"{GAMMA_API}/events"
    params = {"slug": market_id}
    try:
        r = session.get(url, params=params, timeout=15)
        if r.status_code == 200:
            events = r.json()
            if events:
                event = events[0]
                # Include markets in the event
                return event
    except requests.RequestException:
        pass
    
    # Try by ID
    url = f"{GAMMA_API}/events/{market_id}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    
    # Try markets endpoint
    url = f"{GAMMA_API}/markets/{market_id}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    
    # Try markets by slug
    url = f"{GAMMA_API}/markets"
    params = {"slug": market_id}
    try:
        r = session.get(url, params=params, timeout=15)
        if r.status_code == 200:
            markets = r.json()
            if markets:
                return markets[0]
    except requests.RequestException:
        pass
    
    return None


def format_market(m, detailed=False):
    """Format market for display"""
    question = m.get("question", m.get("title", "Unknown"))
    
    # Get outcomes and prices
    outcomes = m.get("outcomes", [])
    tokens = m.get("tokens", [])
    
    # Parse prices
    yes_price = None
    no_price = None
    
    if tokens:
        for t in tokens:
            outcome = t.get("outcome", "").lower()
            price = t.get("price")
            if outcome == "yes" and price:
                yes_price = float(price)
            elif outcome == "no" and price:
                no_price = float(price)
    
    # Fallback to outcomePrices (may be JSON string)
    if not yes_price:
        prices = m.get("outcomePrices", [])
        # Handle JSON string format
        if isinstance(prices, str):
            try:
                prices = json.loads(prices)
            except:
                prices = []
        if len(prices) >= 2:
            try:
                yes_price = float(prices[0]) if prices[0] else None
                no_price = float(prices[1]) if prices[1] else None
            except (ValueError, TypeError):
                pass
    
    # Format prices
    if yes_price is not None:
        yes_pct = f"{yes_price*100:.1f}%"
        no_pct = f"{(1-yes_price)*100:.1f}%" if no_price is None else f"{no_price*100:.1f}%"
    else:
        yes_pct = "?"
        no_pct = "?"
    
    # Volume
    vol = m.get("volumeNum", m.get("volume", 0))
    try:
        vol = float(vol)
    except (ValueError, TypeError):
        vol = 0
    vol_24h = m.get("volume24hr", 0)
    if vol >= 1_000_000:
        vol_str = f"${vol/1_000_000:.1f}M"
    elif vol >= 1_000:
        vol_str = f"${vol/1_000:.0f}K"
    else:
        vol_str = f"${vol:.0f}"
    
    # End date
    end_date = m.get("endDate", m.get("end_date_iso"))
    if end_date:
        try:
            dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            end_str = dt.strftime("%b %d, %Y")
        except:
            end_str = end_date[:10]
    else:
        end_str = "?"
    
    output = f"""
[MARKET] {question}
   YES: {yes_pct} | NO: {no_pct}
   Volume: {vol_str} | Ends: {end_str}"""
    
    if detailed:
        market_id = m.get("id", m.get("condition_id", "?"))
        slug = m.get("slug", "")
        
        # Token IDs for trading
        token_info = ""
        if tokens:
            for t in tokens:
                token_info += f"\n   Token ({t.get('outcome', '?')}): {t.get('token_id', '?')}"
        else:
            # Try clobTokenIds (JSON string)
            clob_tokens = m.get("clobTokenIds", "[]")
            if isinstance(clob_tokens, str):
                try:
                    clob_tokens = json.loads(clob_tokens)
                except:
                    clob_tokens = []
            outcomes_raw = m.get("outcomes", "[]")
            if isinstance(outcomes_raw, str):
                try:
                    outcomes_list = json.loads(outcomes_raw)
                except:
                    outcomes_list = ["Yes", "No"]
            else:
                outcomes_list = outcomes_raw or ["Yes", "No"]
            for i, tok in enumerate(clob_tokens):
                outcome_name = outcomes_list[i] if i < len(outcomes_list) else f"Outcome {i}"
                token_info += f"\n   Token ({outcome_name}): {tok}"
        
        output += f"""
   Market ID: {market_id}
   Slug: {slug}{token_info}
   URL: https://polymarket.com/event/{slug}"""
    
    return output


def main():
    parser = argparse.ArgumentParser(description="Search Polymarket markets")
    parser.add_argument("action", choices=["search", "trending", "category", "detail"],
                       help="Action to perform")
    parser.add_argument("query", nargs="?", default="",
                       help="Search query, category name, or market ID")
    parser.add_argument("--limit", "-n", type=int, default=10,
                       help="Number of results")
    
    args = parser.parse_args()
    
    if args.action == "search":
        if not args.query:
            print("Error: search requires a query")
            sys.exit(1)
        markets = search_markets(args.query, args.limit)
        print(f"=== Search: '{args.query}' ({len(markets)} results) ===")
        for m in markets:
            print(format_market(m))
    
    elif args.action == "trending":
        markets = get_trending(args.limit)
        print(f"=== Trending Markets ({len(markets)}) ===")
        for m in markets:
            print(format_market(m))
    
    elif args.action == "category":
        if not args.query:
            print("Error: category requires a category name")
            print("Options: politics, crypto, sports, entertainment, science, business, finance")
            sys.exit(1)
        markets = get_by_category(args.query, args.limit)
        print(f"=== {args.query.title()} Markets ({len(markets)}) ===")
        for m in markets:
            print(format_market(m))
    
    elif args.action == "detail":
        if not args.query:
            print("Error: detail requires a market ID or slug")
            sys.exit(1)
        market = get_market_detail(args.query)
        if market:
            print("=== Market Detail ===")
            print(format_market(market, detailed=True))
        else:
            print(f"Market not found: {args.query}")


if __name__ == "__main__":
    main()
