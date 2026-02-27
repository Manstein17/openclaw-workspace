#!/usr/bin/env python3
"""
Mert Sniper - 同步交易版本
同时在模拟盘和实盘交易

用法:
    python mert_sniper_sync.py --live
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
import subprocess

sys.stdout.reconfigure(line_buffering=True)

# =============================================================================
# Configuration
# =============================================================================

API_KEY = os.environ.get("SIMMER_API_KEY", "sk_live_XXXXX_REDACTED")
WALLET_PRIVATE_KEY = os.environ.get("WALLET_PRIVATE_KEY", "")
SIMMER_API = "https://api.simmer.markets"

# Trading parameters
MIN_SPLIT = 0.50
MAX_SPLIT = 0.70
MAX_BET_USD = 5.0
EXPIRY_WINDOW = 3

# =============================================================================
# API Helpers
# =============================================================================

def sdk_request(api_key, method, endpoint, data=None):
    """Make API request to Simmer."""
    url = f"{SIMMER_API}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        if method == "GET":
            req = Request(url, headers=headers)
        else:
            req = Request(url, data=json.dumps(data).encode(), headers=headers, method=method)
        
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        print(f"  HTTP Error: {e.code} - {e.read().decode()}")
        return {"error": str(e)}
    except URLError as e:
        print(f"  URL Error: {e.reason}")
        return {"error": str(e)}

def get_markets():
    """Fetch active markets."""
    return sdk_request(API_KEY, "GET", "/api/sdk/markets?status=active&limit=100")

def check_split(yes_price, no_price):
    """Check if market has strong split."""
    if yes_price > no_price:
        split = yes_price * 100
        return ("YES", no_price, split) if split >= MIN_SPLIT * 100 and split <= MAX_SPLIT * 100 else None
    else:
        split = no_price * 100
        return ("NO", yes_price, split) if split >= MIN_SPLIT * 100 and split <= MAX_SPLIT * 100 else None

def execute_trade(venue, market_id, side, amount, reasoning=""):
    """Execute trade on specified venue."""
    return sdk_request(API_KEY, "POST", "/api/sdk/trade", {
        "market_id": market_id,
        "side": side,
        "amount": amount,
        "venue": venue,
        "source": "mert-sniper-sync",
        "reasoning": reasoning,
    })

# =============================================================================
# Main
# =============================================================================

def main():
    print("🎯 Mert Sniper - 同步交易")
    print("=" * 50)
    
    live = "--live" in sys.argv or "-l" in sys.argv
    
    if live:
        print(f"\n  模式: 🔴 实盘 + 模拟盘 同步")
    else:
        print(f"\n  模式: 🟡 模拟测试 (无实际交易)")
    
    print(f"\n  参数: min_split={MIN_SPLIT}, max_split={MAX_SPLIT}, max_bet=${MAX_BET_USD}")
    
    # Get markets
    print(f"\n  扫描市场...")
    result = get_markets()
    
    if "error" in result:
        print(f"  ❌ 获取市场失败: {result['error']}")
        return
    
    markets = result.get("markets", [])
    print(f"  找到 {len(markets)} 个活跃市场")
    
    now = datetime.now(timezone.utc)
    opportunities = []
    
    for market in markets:
        try:
            question = market.get("question", "")
            ends_at = market.get("endsAt") or market.get("endDate")
            if not ends_at:
                continue
            
            end_time = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
            minutes_left = (end_time - now).total_seconds() / 60
            
            if minutes_left > EXPIRY_WINDOW or minutes_left < 0:
                continue
            
            yes_price = float(market.get("yesPrice", 0) or market.get("current_probability", 0))
            no_price = float(market.get("noPrice", 0) or (1 - float(market.get("current_probability", 0.5))))
            
            if yes_price == 0 or no_price == 0:
                continue
            
            result = check_split(yes_price, no_price)
            if result:
                side, opp_price, split = result
                opportunities.append({
                    "question": question[:50],
                    "minutes_left": minutes_left,
                    "side": side,
                    "price": opp_price,
                    "split": split,
                    "market_id": market.get("id")
                })
        
        except Exception as e:
            continue
    
    print(f"\n  找到 {len(opportunities)} 个机会")
    
    if not opportunities:
        print("  无交易机会")
        return
    
    # Execute on BOTH venues simultaneously
    for opp in opportunities[:3]:  # Max 3 trades
        amount = MAX_BET_USD / opp["price"]
        reasoning = f"Mert Sniper: {opp['split']:.0f}% split on {opp['question']}"
        
        print(f"\n  📊 {opp['question']}...")
        print(f"     分歧: {opp['split']:.0f}% | 方向: {opp['side']} @ ${opp['price']:.2f}")
        
        # Simmer (always)
        if not live:
            print(f"     🟡 模拟盘: 买入 {amount:.2f} {opp['side']} (dry-run)")
        else:
            result_sim = execute_trade("simmer", opp["market_id"], opp["side"], MAX_BET_USD, reasoning)
            if "error" in result_sim:
                print(f"     ❌ 模拟盘失败: {result_sim['error']}")
            else:
                shares = result_sim.get("shares_bought", amount)
                print(f"     ✅ 模拟盘: 买入 {shares:.2f} {opp['side']}")
        
        # Polymarket (only with --live)
        if not live:
            print(f"     🟡 实盘: 买入 {amount:.2f} {opp['side']} (dry-run)")
        else:
            if not WALLET_PRIVATE_KEY:
                print(f"     ⚠️ 实盘: 需要设置 WALLET_PRIVATE_KEY")
            else:
                result_live = execute_trade("polymarket", opp["market_id"], opp["side"], MAX_BET_USD, reasoning)
                if "error" in result_live:
                    print(f"     ❌ 实盘失败: {result_live['error']}")
                else:
                    shares = result_live.get("shares_bought", amount)
                    print(f"     ✅ 实盘: 买入 {shares:.2f} {opp['side']}")

if __name__ == "__main__":
    main()
