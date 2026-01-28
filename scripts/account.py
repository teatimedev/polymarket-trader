#!/usr/bin/env python3
"""
Account info - check balance, positions, and allowances
"""

import os
import sys
import json
import requests
from requests.adapters import HTTPAdapter, Retry

# Add venv to path (version-agnostic)
VENV_BASE = os.path.expanduser("~/polymarket-venv/lib")
if os.path.exists(VENV_BASE):
    for entry in os.listdir(VENV_BASE):
        if entry.startswith("python"):
            site_packages = os.path.join(VENV_BASE, entry, "site-packages")
            if site_packages not in sys.path:
                sys.path.insert(0, site_packages)
            break

from eth_account import Account
from py_clob_client.client import ClobClient


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


def get_client():
    """Initialize authenticated CLOB client"""
    pk = os.environ.get("POLYMARKET_PRIVATE_KEY")
    if not pk:
        print("Error: POLYMARKET_PRIVATE_KEY not set")
        sys.exit(1)
    
    account = Account.from_key(pk)
    funder = os.environ.get("POLYMARKET_FUNDER", account.address)
    
    client = ClobClient(
        host="https://clob.polymarket.com",
        chain_id=137,
        key=pk,
        signature_type=0,  # EOA (direct wallet) for Magic Link
    )
    
    # Get API credentials
    creds = client.derive_api_key()
    client.set_api_creds(creds)
    
    return client, account.address, funder


def get_positions(address):
    """Get positions from data API"""
    session = get_session()
    url = f"https://data-api.polymarket.com/positions?user={address.lower()}"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error fetching positions: {e}")
    return []


def get_trades(address, limit=10):
    """Get recent trades"""
    session = get_session()
    url = f"https://data-api.polymarket.com/trades?user={address.lower()}&limit={limit}"
    try:
        r = session.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Error fetching trades: {e}")
    return []


def main():
    client, address, funder = get_client()
    
    print(f"=== Polymarket Account ===")
    print(f"Signing Address: {address}")
    print(f"Funder Address:  {funder}")
    print()
    
    # Get positions (check signing address - that's where positions are tracked)
    positions = get_positions(address)
    if not positions:
        # Fallback to funder address
        positions = get_positions(funder)
    if positions:
        print(f"=== Positions ({len(positions)}) ===")
        total_value = 0
        for p in positions:
            title = p.get("title", p.get("question", "Unknown"))[:50]
            size = float(p.get("size", 0))
            avg_price = float(p.get("avgPrice", 0))
            cur_price = float(p.get("curPrice", avg_price))
            outcome = p.get("outcome", "?")
            value = size * cur_price
            pnl = (cur_price - avg_price) * size
            total_value += value
            pnl_str = f"+${pnl:.2f}" if pnl >= 0 else f"-${abs(pnl):.2f}"
            print(f"  {outcome}: {title}...")
            print(f"      Size: {size:.2f} @ ${avg_price:.3f} -> ${cur_price:.3f} ({pnl_str})")
        print(f"\nTotal Position Value: ${total_value:.2f}")
    else:
        print("No open positions")
    print()
    
    # Get open orders
    try:
        orders = client.get_orders()
        if orders:
            print(f"=== Open Orders ({len(orders)}) ===")
            for o in orders[:10]:
                print(f"  {o.get('side', '?')} {o.get('size', '?')} @ {o.get('price', '?')}")
        else:
            print("No open orders")
    except Exception as e:
        print(f"Could not fetch orders: {e}")
    print()
    
    # Recent trades
    trades = get_trades(funder, limit=5)
    if trades:
        print(f"=== Recent Trades ===")
        for t in trades[:5]:
            side = t.get("side", "?")
            size = t.get("size", "?")
            price = t.get("price", "?")
            title = t.get("title", t.get("question", "Unknown"))[:40]
            print(f"  {side} {size} @ ${price} - {title}...")
    

if __name__ == "__main__":
    main()
