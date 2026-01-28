#!/usr/bin/env python3
"""
Autonomous Polymarket Trader
Finds short-term markets, researches them, and makes trades.
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add venv to path
VENV_PATH = os.path.expanduser("~/polymarket-venv/lib/python3.12/site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

import requests
from eth_account import Account
from py_clob_client.client import ClobClient

SKILL_DIR = Path(__file__).parent.parent
CONFIG_PATH = SKILL_DIR / "config.json"
STATE_PATH = SKILL_DIR / "state.json"
GAMMA_API = "https://gamma-api.polymarket.com"


def load_config():
    """Load trading configuration"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def load_state():
    """Load trading state (positions, P&L tracking)"""
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {
        "trades": [],
        "daily_pnl": 0,
        "last_reset": datetime.now(timezone.utc).isoformat(),
        "total_invested": 0
    }


def save_state(state):
    """Save trading state"""
    with open(STATE_PATH, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def get_client():
    """Initialize CLOB client"""
    pk = os.environ.get("POLYMARKET_PRIVATE_KEY")
    if not pk:
        return None
    
    account = Account.from_key(pk)
    funder = os.environ.get("POLYMARKET_FUNDER", account.address)
    
    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,
        key=pk,
        signature_type=0,  # EOA
        funder=funder
    )
    
    creds = client.derive_api_key()
    client.set_api_creds(creds)
    return client


def find_expiring_markets(max_days=7, min_hours=6, limit=50):
    """Find markets expiring within the specified window"""
    now = datetime.now(timezone.utc)
    max_date = now + timedelta(days=max_days)
    min_date = now + timedelta(hours=min_hours)
    
    # Fetch active events
    url = f"{GAMMA_API}/events"
    params = {
        "active": "true",
        "closed": "false",
        "limit": 200
    }
    
    r = requests.get(url, params=params, timeout=30)
    if r.status_code != 200:
        return []
    
    events = r.json()
    expiring = []
    
    for event in events:
        end_date_str = event.get("endDate")
        if not end_date_str:
            continue
        
        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
        except:
            continue
        
        # Check if within our window
        if min_date <= end_date <= max_date:
            # Get volume
            volume = float(event.get("volume", 0) or 0)
            
            # Get markets from event
            markets = event.get("markets", [])
            for m in markets:
                m["event_title"] = event.get("title")
                m["event_end_date"] = end_date
                m["event_volume"] = volume
                m["hours_to_expiry"] = (end_date - now).total_seconds() / 3600
                expiring.append(m)
    
    # Sort by volume (most liquid first)
    expiring.sort(key=lambda x: x.get("event_volume", 0), reverse=True)
    return expiring[:limit]


def research_market(question, context=""):
    """Use exa-search to research a market question"""
    # Build research query
    query = f"{question} latest news prediction"
    
    try:
        result = subprocess.run([
            "mcporter", "call",
            "https://mcp.exa.ai/mcp?tools=deep_search_exa",
            "deep_search_exa",
            f"query={query}"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        print(f"Research error: {e}")
    
    return ""


def evaluate_opportunity(market, research_text, config):
    """
    Evaluate if a market presents a trading opportunity.
    Returns: (should_trade, side, confidence, reasoning)
    """
    question = market.get("question", market.get("event_title", ""))
    
    # Parse current prices
    prices_str = market.get("outcomePrices", "[]")
    try:
        if isinstance(prices_str, str):
            prices = json.loads(prices_str)
        else:
            prices = prices_str or []
        yes_price = float(prices[0]) if prices else 0.5
    except:
        yes_price = 0.5
    
    no_price = 1 - yes_price
    
    # Simple heuristic: look for extreme odds that research might contradict
    # This is where you'd add more sophisticated analysis
    
    analysis = {
        "question": question,
        "yes_price": yes_price,
        "no_price": no_price,
        "research_summary": research_text[:500] if research_text else "No research available",
        "hours_to_expiry": market.get("hours_to_expiry", 0)
    }
    
    # Conservative default: don't trade unless we find something compelling
    # In practice, you'd want ML or more sophisticated analysis here
    
    # Example heuristic: if odds are very extreme (>95% or <5%), be skeptical
    if yes_price > 0.95 or yes_price < 0.05:
        # Extreme odds - potentially interesting if research suggests otherwise
        if research_text and len(research_text) > 100:
            # We have research - flag for review
            return (False, None, 0.5, f"Extreme odds ({yes_price*100:.1f}% YES) - needs human review")
    
    # For now, return conservative "no trade" - the human can override
    return (False, None, 0.3, "Insufficient confidence for autonomous trade")


def format_opportunity_report(markets, evaluations):
    """Format a report of potential opportunities"""
    report = []
    report.append("=== Polymarket Opportunities Report ===")
    report.append(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    report.append(f"Markets expiring soon: {len(markets)}")
    report.append("")
    
    for market, eval_result in zip(markets[:10], evaluations[:10]):
        should_trade, side, confidence, reasoning = eval_result
        
        question = market.get("question", market.get("event_title", "Unknown"))[:60]
        hours = market.get("hours_to_expiry", 0)
        volume = market.get("event_volume", 0)
        
        prices_str = market.get("outcomePrices", "[]")
        try:
            prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str or []
            yes_price = float(prices[0]) if prices else 0.5
        except:
            yes_price = 0.5
        
        status = "🟢 TRADE" if should_trade else "⚪ WATCH"
        
        report.append(f"{status} {question}...")
        report.append(f"   YES: {yes_price*100:.1f}% | Expires: {hours:.0f}h | Vol: ${volume/1000:.0f}K")
        report.append(f"   → {reasoning}")
        report.append("")
    
    return "\n".join(report)


def main():
    print("=== Polymarket Auto-Trader ===")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print()
    
    config = load_config()
    state = load_state()
    
    budget = config.get("budget", {})
    strategy = config.get("strategy", {})
    
    print(f"Budget: ${budget.get('total_usd', 25)} | Max/trade: ${budget.get('max_per_trade_usd', 10)}")
    print(f"Looking for markets expiring in {strategy.get('min_expiry_hours', 6)}-{strategy.get('max_expiry_days', 7)*24}h")
    print()
    
    # Find expiring markets
    markets = find_expiring_markets(
        max_days=strategy.get("max_expiry_days", 7),
        min_hours=strategy.get("min_expiry_hours", 6)
    )
    
    print(f"Found {len(markets)} markets expiring soon")
    
    if not markets:
        print("No suitable markets found")
        return
    
    # Evaluate top markets
    evaluations = []
    for market in markets[:10]:
        question = market.get("question", market.get("event_title", ""))
        print(f"\nAnalyzing: {question[:50]}...")
        
        # Research (disabled by default to save API calls - enable when ready)
        # research = research_market(question)
        research = ""
        
        eval_result = evaluate_opportunity(market, research, config)
        evaluations.append(eval_result)
    
    # Generate report
    report = format_opportunity_report(markets, evaluations)
    print("\n" + report)
    
    # Save state
    state["last_scan"] = datetime.now(timezone.utc).isoformat()
    state["markets_found"] = len(markets)
    save_state(state)
    
    return report


if __name__ == "__main__":
    main()
