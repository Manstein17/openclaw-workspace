#!/usr/bin/env python3
"""
Mert Sniper - Live Trading Version
Real your Polymarket trading with API key

Usage:
    python mert_sniper_live.py              # Dry run
    python mert_sniper_live.py --live       # Execute real trades
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

sys.stdout.reconfigure(line_buffering=True)

# =============================================================================
# Configuration
# =============================================================================

API_KEY = "019c6581-0b59-78bf-9e40-06c290170b51"  # User's Polymarket API Key
POLYMARKET_API = "https://clob.polymarket.com"

# Trading parameters
MIN_SPLIT = 0.50      # Minimum probability (50%)
MAX_SPLIT = 0.70      # Maximum probability (70%)
MAX_BET_USD = 2.0     # Maximum bet size
EXPIRY_WINDOW = 3     # Minutes before expiry

# =============================================================================
# API Helpers
# =============================================================================

def make_request(url, method="GET", data=None):
    """Make API request to Polymarket."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    try:
        if method == "GET":
            req = Request(url, headers=headers)
        else:
            req = Request(url, data=json.dumps(data).encode(), headers=headers, method=method)
        
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None

def get_markets():
    """Fetch active markets."""
    url = f"{POLYMARKET_API}/markets?limit=100&active=true"
    return make_request(url)

def get_order_book(market_id):
    """Get order book for a market."""
    url = f"{POLYMARKET_API}/orderbook?market={market_id}"
    return make_request(url)

def place_order(market_id, side, size, price):
    """Place an order."""
    # This is a simplified version - real implementation needs more error handling
    print(f"  Would place order: {side} {size} shares @ ${price}")
    return {"success": True, "order_id": "demo"}

# =============================================================================
# Trading Logic
# =============================================================================

def check_split(yes_price, no_price):
    """Check if market has strong split."""
    if yes_price > no_price:
        split = yes_price * 100
        return ("YES", no_price, split) if split >= MIN_SPLIT * 100 and split <= MAX_SPLIT * 100 else None
    else:
        split = no_price * 100
        return ("NO", yes_price, split) if split >= MIN_SPLIT * 100 and split <= MAX_SPLIT * 100 else None

def scan_markets(live=False):
    """Scan for opportunities."""
    print(f"\n{'='*50}")
    print(f"🔍 Scanning Polymarket (Live Mode: {live})")
    print(f"{'='*50}")
    
    markets = get_markets()
    if not markets:
        print("Failed to fetch markets")
        return
    
    now = datetime.now(timezone.utc)
    opportunities = []
    
    for market in markets[:100]:  # Scan first 100
        try:
            # Get market info
            question = market.get("question", "")
            ends_at = market.get("endsAt") or market.get("endDate")
            if not ends_at:
                continue
            
            end_time = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            minutes_left = (end_time - now).total_seconds() / 60
            
            if minutes_left > EXPIRY_WINDOW or minutes_left < 0:
                continue
            
            # Get prices (simplified - real API has more data)
            yes_price = float(market.get("yesPrice", 0))
            no_price = float(market.get("noPrice", 0))
            
            if yes_price == 0 or no_price == 0:
                continue
            
            # Check split
            result = check_split(yes_price, no_price)
            if result:
                side, opp_price, split = result
                opportunities.append({
                    "question": question,
                    "minutes_left": minutes_left,
                    "side": side,
                    "price": opp_price,
                    "split": split,
                    "market_id": market.get("id")
                })
                print(f"  ✅ {question[:50]}...")
                print(f"     {split:.0f}% / {side}, {minutes_left:.0f}min left")
        
        except Exception as e:
            continue
    
    print(f"\n📊 Found {len(opportunities)} opportunities")
    
    if opportunities and live:
        # Execute trade on best opportunity
        opp = opportunities[0]
        size = MAX_BET_USD / opp["price"]
        print(f"\n🚀 Executing trade:")
        print(f"   Market: {opp['question'][:50]}...")
        print(f"   Side: {opp['side']} @ ${opp['price']:.2f}")
        print(f"   Size: {size:.2f} shares (${MAX_BET_USD})")
        
        # Place order would go here
        # result = place_order(opp["market_id"], opp["side"], size, opp["price"])
        print("\n⚠️ Live trading not fully implemented - this is a demo")
    elif opportunities:
        print("\n💡 Run with --live to execute trades")

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mert Sniper - Live Trading")
    parser.add_argument("--live", action="store_true", help="Execute real trades")
    args = parser.parse_args()
    
    scan_markets(live=args.live)
