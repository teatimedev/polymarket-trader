#!/usr/bin/env python3
"""
Manage open orders
"""

import os
import sys
import argparse

# Add venv to path
VENV_PATH = os.path.expanduser("~/polymarket-venv/lib/python3.12/site-packages")
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

from eth_account import Account
from py_clob_client.client import ClobClient


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
        signature_type=0,  # EOA
    )
    
    creds = client.derive_api_key()
    client.set_api_creds(creds)
    
    return client


def list_orders(client):
    """List all open orders"""
    try:
        orders = client.get_orders()
        if not orders:
            print("No open orders")
            return
        
        print(f"=== Open Orders ({len(orders)}) ===")
        for o in orders:
            order_id = o.get("id", "?")[:12]
            side = o.get("side", "?")
            price = o.get("price", "?")
            size = o.get("original_size", o.get("size", "?"))
            filled = o.get("size_matched", 0)
            remaining = float(size) - float(filled) if size != "?" else "?"
            
            print(f"\n  Order: {order_id}...")
            print(f"    {side} @ ${price}")
            print(f"    Size: {size} | Filled: {filled} | Remaining: {remaining}")
            
    except Exception as e:
        print(f"Error listing orders: {e}")


def cancel_order(client, order_id):
    """Cancel a specific order"""
    try:
        result = client.cancel(order_id)
        print(f"✅ Order cancelled: {order_id}")
        return result
    except Exception as e:
        print(f"❌ Error cancelling order: {e}")
        return None


def cancel_all(client):
    """Cancel all open orders"""
    try:
        result = client.cancel_all()
        print(f"✅ All orders cancelled")
        return result
    except Exception as e:
        print(f"❌ Error cancelling orders: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Manage Polymarket orders")
    parser.add_argument("action", choices=["list", "cancel", "cancel-all"],
                       help="Action to perform")
    parser.add_argument("order_id", nargs="?",
                       help="Order ID (for cancel)")
    
    args = parser.parse_args()
    client = get_client()
    
    if args.action == "list":
        list_orders(client)
    
    elif args.action == "cancel":
        if not args.order_id:
            print("Error: order_id required for cancel")
            sys.exit(1)
        cancel_order(client, args.order_id)
    
    elif args.action == "cancel-all":
        confirm = input("Cancel ALL open orders? (yes/no): ").strip().lower()
        if confirm == "yes":
            cancel_all(client)
        else:
            print("Cancelled")


if __name__ == "__main__":
    main()
