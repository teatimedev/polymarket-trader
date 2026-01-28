#!/usr/bin/env python3
"""
Place trades on Polymarket
"""

import os
import sys
import argparse
import json
import re

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
from py_clob_client.clob_types import OrderArgs, OrderType, PartialCreateOrderOptions


def validate_token_id(token_id: str) -> bool:
    """Validate token ID format (should be numeric string or hex)"""
    if not token_id:
        return False
    # Polymarket token IDs are typically large integers
    if re.match(r'^\d+$', token_id):
        return True
    # Or hex format
    if re.match(r'^0x[a-fA-F0-9]+$', token_id):
        return True
    return False


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
        signature_type=0,  # EOA (direct wallet) - works for MetaMask
        # Note: Don't set funder for EOA accounts
    )
    
    # Get API credentials
    creds = client.derive_api_key()
    client.set_api_creds(creds)
    
    return client


def place_order(client, token_id, side, price, size, order_type="limit"):
    """Place a limit or market order"""
    
    # Build order args
    order_args = OrderArgs(
        token_id=token_id,
        price=price,
        size=size,
        side=side.upper()  # BUY or SELL
    )
    
    # Create order options with tick_size
    options = PartialCreateOrderOptions(
        tick_size="0.01",
        neg_risk=False
    )
    
    try:
        # Create and post the order
        result = client.create_and_post_order(order_args, options)
        return result
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Trade on Polymarket")
    parser.add_argument("action", choices=["buy", "sell"],
                       help="Buy or sell")
    parser.add_argument("token_id",
                       help="Token ID to trade (get from markets.py detail)")
    parser.add_argument("--price", "-p", type=float,
                       help="Limit price (0.01-0.99)")
    parser.add_argument("--size", "-s", type=float, required=True,
                       help="Size in USDC")
    parser.add_argument("--market", "-m", action="store_true",
                       help="Market order (take best available)")
    parser.add_argument("--side", choices=["YES", "NO"], default="YES",
                       help="YES or NO outcome (default: YES)")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show order details without executing")
    parser.add_argument("--yes", "-y", action="store_true",
                       help="Skip confirmation prompt (for automated trading)")
    
    args = parser.parse_args()
    
    # Validate token ID
    if not validate_token_id(args.token_id):
        print(f"Error: Invalid token ID format: {args.token_id}")
        print("Token IDs should be numeric (e.g., '123456789') or hex (e.g., '0xabc123')")
        sys.exit(1)
    
    # Validate price for limit orders
    if not args.market and args.price is None:
        print("Error: --price required for limit orders (use --market for market orders)")
        sys.exit(1)
    
    if args.price and (args.price < 0.01 or args.price > 0.99):
        print("Error: price must be between 0.01 and 0.99")
        sys.exit(1)
    
    # Build order details
    side = "BUY" if args.action == "buy" else "SELL"
    price = args.price if args.price else 0.99 if side == "BUY" else 0.01
    order_type = "market" if args.market else "limit"
    
    print(f"=== Order Details ===")
    print(f"Action: {side} {args.side}")
    print(f"Token ID: {args.token_id}")
    print(f"Price: ${price:.2f}")
    print(f"Size: ${args.size:.2f} USDC")
    print(f"Type: {order_type}")
    print()
    
    if args.dry_run:
        print("(Dry run - order not placed)")
        return
    
    # Confirm (skip if --yes flag)
    if not args.yes:
        confirm = input("Place order? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Order cancelled")
            return
    
    client = get_client()
    result = place_order(client, args.token_id, side, price, args.size, order_type)
    
    if "error" in result:
        print(f"X Order failed: {result['error']}")
    else:
        print(f"OK Order placed!")
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
