#!/usr/bin/env python3
"""
Polymarket Opportunity Scanner
Systematically scans ALL active markets to find trading opportunities.
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

GAMMA_API = "https://gamma-api.polymarket.com"

def fetch_all_active_markets(limit: int = 500) -> List[Dict]:
    """Fetch all active markets from Polymarket"""
    all_markets = []
    offset = 0
    batch_size = 100
    
    while len(all_markets) < limit:
        url = f"{GAMMA_API}/markets"
        params = {
            "limit": batch_size,
            "offset": offset,
            "active": "true",
            "closed": "false",
            "order": "volume24hr",
            "ascending": "false"
        }
        
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code != 200:
                break
            
            markets = r.json()
            if not markets:
                break
                
            all_markets.extend(markets)
            offset += batch_size
            
            # If we got fewer than batch_size, we've hit the end
            if len(markets) < batch_size:
                break
                
        except Exception as e:
            print(f"Error fetching markets: {e}", file=sys.stderr)
            break
    
    return all_markets[:limit]


def parse_market_data(m: Dict) -> Optional[Dict]:
    """Parse market into standardized format with all relevant data"""
    try:
        question = m.get("question", m.get("title", ""))
        if not question:
            return None
        
        # Parse prices
        yes_price = None
        no_price = None
        
        tokens = m.get("tokens", [])
        if tokens:
            for t in tokens:
                outcome = t.get("outcome", "").lower()
                price = t.get("price")
                if outcome == "yes" and price:
                    yes_price = float(price)
                elif outcome == "no" and price:
                    no_price = float(price)
        
        # Fallback to outcomePrices
        if yes_price is None:
            prices = m.get("outcomePrices", [])
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
        
        if yes_price is None:
            return None
        
        # Volume
        vol = m.get("volumeNum", m.get("volume", 0))
        try:
            vol = float(vol)
        except (ValueError, TypeError):
            vol = 0
        
        vol_24h = m.get("volume24hr", 0)
        try:
            vol_24h = float(vol_24h)
        except (ValueError, TypeError):
            vol_24h = 0
        
        # Liquidity
        liquidity = m.get("liquidity", 0)
        try:
            liquidity = float(liquidity)
        except (ValueError, TypeError):
            liquidity = 0
        
        # End date
        end_date = m.get("endDate", m.get("end_date_iso"))
        end_dt = None
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except:
                pass
        
        # Token IDs for trading
        token_ids = {}
        if tokens:
            for t in tokens:
                token_ids[t.get("outcome", "").lower()] = t.get("token_id")
        else:
            clob_tokens = m.get("clobTokenIds", "[]")
            if isinstance(clob_tokens, str):
                try:
                    clob_tokens = json.loads(clob_tokens)
                except:
                    clob_tokens = []
            if len(clob_tokens) >= 2:
                token_ids["yes"] = clob_tokens[0]
                token_ids["no"] = clob_tokens[1]
        
        return {
            "question": question,
            "slug": m.get("slug", ""),
            "market_id": m.get("id", m.get("condition_id", "")),
            "yes_price": yes_price,
            "no_price": no_price if no_price else (1 - yes_price),
            "volume": vol,
            "volume_24h": vol_24h,
            "liquidity": liquidity,
            "end_date": end_dt,
            "token_ids": token_ids,
            "url": f"https://polymarket.com/event/{m.get('slug', '')}"
        }
    except Exception as e:
        return None


def categorize_market(question: str) -> str:
    """Attempt to categorize market by keywords"""
    q = question.lower()
    
    # Sports
    sports_keywords = ["nba", "nfl", "nhl", "mlb", "premier league", "champions league", 
                       "vs.", "game", "match", "winner", "playoff", "super bowl", 
                       "world cup", "olympics", "tennis", "golf", "f1", "formula",
                       "boxing", "ufc", "mma", "spread:", "o/u", "lol:", "esports"]
    if any(k in q for k in sports_keywords):
        return "sports"
    
    # Crypto
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth", "crypto", "solana", "sol",
                       "token", "blockchain", "defi", "nft", "altcoin", "memecoin"]
    if any(k in q for k in crypto_keywords):
        return "crypto"
    
    # Politics
    politics_keywords = ["president", "election", "congress", "senate", "house", 
                         "democrat", "republican", "vote", "governor", "mayor",
                         "trump", "biden", "cabinet", "nomination", "supreme court",
                         "impeach", "legislation", "bill pass"]
    if any(k in q for k in politics_keywords):
        return "politics"
    
    # Economics/Fed
    econ_keywords = ["fed", "interest rate", "inflation", "gdp", "unemployment",
                     "recession", "fomc", "treasury", "tariff", "trade"]
    if any(k in q for k in econ_keywords):
        return "economics"
    
    # Geopolitics
    geo_keywords = ["war", "strike", "invasion", "military", "iran", "russia", 
                    "china", "ukraine", "israel", "gaza", "hamas", "nato", "sanctions"]
    if any(k in q for k in geo_keywords):
        return "geopolitics"
    
    # Tech/AI
    tech_keywords = ["ai", "openai", "google", "apple", "tesla", "amazon", "meta",
                     "microsoft", "chatgpt", "model", "launch", "acquisition"]
    if any(k in q for k in tech_keywords):
        return "tech"
    
    # Entertainment
    ent_keywords = ["oscar", "grammy", "emmy", "movie", "album", "celebrity",
                    "kardashian", "taylor swift", "elon musk tweet"]
    if any(k in q for k in ent_keywords):
        return "entertainment"
    
    return "other"


def score_opportunity(market: Dict) -> float:
    """
    Score a market for trading opportunity.
    Higher score = more interesting opportunity.
    
    Factors:
    - Odds between 20-80% (room for edge, not already decided)
    - Volume/liquidity (can actually trade)
    - Reasonable time to resolution
    - Not pure gambling (sports point spreads are harder)
    """
    score = 0.0
    
    yes_price = market["yes_price"]
    
    # Odds factor: prefer 20-80% range, peak at 50%
    # Avoid near-certain outcomes (less edge potential)
    if 0.20 <= yes_price <= 0.80:
        # Parabola peaking at 0.5
        odds_score = 1 - 4 * (yes_price - 0.5) ** 2
        score += odds_score * 30
    elif 0.10 <= yes_price <= 0.90:
        score += 10
    else:
        score += 0  # Too extreme
    
    # Volume factor (log scale)
    import math
    vol = market["volume"]
    if vol > 0:
        vol_score = min(math.log10(vol + 1) / 6, 1)  # Cap at ~$1M
        score += vol_score * 25
    
    # 24h volume bonus (active trading)
    vol_24h = market["volume_24h"]
    if vol_24h > 10000:
        score += 10
    elif vol_24h > 1000:
        score += 5
    
    # Liquidity factor
    liq = market["liquidity"]
    if liq > 50000:
        score += 15
    elif liq > 10000:
        score += 10
    elif liq > 1000:
        score += 5
    
    # Time to resolution factor
    end_date = market["end_date"]
    if end_date:
        now = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.utcnow()
        days_left = (end_date - now).days
        
        if 1 <= days_left <= 30:
            # Sweet spot: resolves soon but not immediately
            score += 20
        elif 30 < days_left <= 90:
            score += 10
        elif days_left <= 0:
            score -= 50  # Already expired
    
    return score


def format_market_summary(m: Dict, score: float) -> str:
    """Format market for display"""
    yes_pct = f"{m['yes_price']*100:.1f}%"
    no_pct = f"{m['no_price']*100:.1f}%"
    
    vol = m["volume"]
    if vol >= 1_000_000:
        vol_str = f"${vol/1_000_000:.1f}M"
    elif vol >= 1_000:
        vol_str = f"${vol/1_000:.0f}K"
    else:
        vol_str = f"${vol:.0f}"
    
    end_str = m["end_date"].strftime("%b %d") if m["end_date"] else "?"
    
    return f"""
📊 {m['question'][:80]}{'...' if len(m['question']) > 80 else ''}
   YES: {yes_pct} | NO: {no_pct}
   Vol: {vol_str} | Ends: {end_str} | Score: {score:.0f}
   🔗 {m['url']}"""


def scan_markets(
    min_volume: float = 10000,
    min_liquidity: float = 1000,
    odds_range: tuple = (0.10, 0.90),
    categories: List[str] = None,
    limit: int = 20,
    exclude_sports: bool = False
) -> List[Dict]:
    """
    Scan all markets and return top opportunities.
    """
    print("🔍 Fetching all active markets...", file=sys.stderr)
    raw_markets = fetch_all_active_markets(500)
    print(f"   Found {len(raw_markets)} raw markets", file=sys.stderr)
    
    # Parse and filter
    parsed = []
    for m in raw_markets:
        pm = parse_market_data(m)
        if pm is None:
            continue
        
        # Volume filter
        if pm["volume"] < min_volume:
            continue
        
        # Liquidity filter
        if pm["liquidity"] < min_liquidity:
            continue
        
        # Odds filter
        if not (odds_range[0] <= pm["yes_price"] <= odds_range[1]):
            continue
        
        # Category
        pm["category"] = categorize_market(pm["question"])
        
        # Category filter
        if categories and pm["category"] not in categories:
            continue
        
        # Exclude sports if requested
        if exclude_sports and pm["category"] == "sports":
            continue
        
        # Score
        pm["score"] = score_opportunity(pm)
        parsed.append(pm)
    
    print(f"   {len(parsed)} markets after filtering", file=sys.stderr)
    
    # Sort by score
    parsed.sort(key=lambda x: x["score"], reverse=True)
    
    return parsed[:limit]


def main():
    parser = argparse.ArgumentParser(description="Scan Polymarket for opportunities")
    parser.add_argument("--limit", "-n", type=int, default=20,
                       help="Number of top opportunities to show")
    parser.add_argument("--min-volume", type=float, default=10000,
                       help="Minimum total volume ($)")
    parser.add_argument("--min-liquidity", type=float, default=1000,
                       help="Minimum liquidity ($)")
    parser.add_argument("--min-odds", type=float, default=0.10,
                       help="Minimum YES price (0-1)")
    parser.add_argument("--max-odds", type=float, default=0.90,
                       help="Maximum YES price (0-1)")
    parser.add_argument("--category", "-c", action="append",
                       help="Filter by category (can repeat)")
    parser.add_argument("--exclude-sports", action="store_true",
                       help="Exclude sports markets")
    parser.add_argument("--json", action="store_true",
                       help="Output as JSON")
    
    args = parser.parse_args()
    
    opportunities = scan_markets(
        min_volume=args.min_volume,
        min_liquidity=args.min_liquidity,
        odds_range=(args.min_odds, args.max_odds),
        categories=args.category,
        limit=args.limit,
        exclude_sports=args.exclude_sports
    )
    
    if args.json:
        # Convert datetime to string for JSON
        for o in opportunities:
            if o["end_date"]:
                o["end_date"] = o["end_date"].isoformat()
        print(json.dumps(opportunities, indent=2))
    else:
        print(f"\n🎯 TOP {len(opportunities)} OPPORTUNITIES\n" + "="*50)
        
        # Group by category
        by_cat = {}
        for o in opportunities:
            cat = o["category"]
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(o)
        
        for cat, markets in sorted(by_cat.items(), key=lambda x: -len(x[1])):
            print(f"\n📁 {cat.upper()} ({len(markets)})")
            for m in markets:
                print(format_market_summary(m, m["score"]))


if __name__ == "__main__":
    main()
