#!/usr/bin/env python3
"""
Simmer Signal Monitor - With Auto-Sell functionality
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/polymarket-elon-tweets"))
from elon_tweets import import_event

# ============== CONFIG ==============
CONFIG = {
    "max_price": 0.20,
    "min_volume": 0,
    "max_position": 1.50,
    "max_positions_per_event": 2,
    "max_trades_per_day": 4,
    "pause_after_loss": 3,
    "stop_loss": 0.30,      # Auto-sell at -30%
    "take_profit": 0.80,    # Auto-sell at +80%
}

# State file
STATE_FILE = os.path.expanduser("~/.openclaw/workspace/.simmer-monitor-state.json")
OPTIMIZE_INTERVAL_DAYS = 3

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "trades_today": [],
        "last_loss_time": None,
        "positions": {},
        "last_optimize": None,
        "trade_history": [],
        "best_params": {}
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def get_journal_positions():
    """Get open positions from trade journal"""
    import subprocess
    result = subprocess.run([
        'python3', os.path.expanduser('~/.openclaw/workspace/scripts/trade-journal.py'), 'status'
    ], capture_output=True, text=True, cwd=os.path.expanduser('~/.openclaw/workspace/scripts'))
    return result.stdout

def check_exit_signals():
    """Check if any positions should be sold"""
    journal_file = os.path.expanduser("~/.openclaw/workspace/.trade-journal.json")
    if not os.path.exists(journal_file):
        return []
    
    with open(journal_file) as f:
        journal = json.load(f)
    
    positions = journal.get("positions", {})
    if not positions:
        return []
    
    # Get current prices
    events = [
        "https://polymarket.com/event/elon-musk-of-tweets-february-27-march-6",
    ]
    
    price_map = {}
    for event_url in events:
        try:
            result = import_event(event_url)
            if result and "markets" in result:
                for m in result["markets"]:
                    price_map[m["market_id"]] = m.get("current_probability", 0)
        except:
            continue
    
    exit_signals = []
    
    for market_id, trade in positions.items():
        current_price = price_map.get(market_id, trade.get("current_price", trade["price"]))
        buy_price = trade["price"]
        
        # Calculate P&L percentage
        if buy_price > 0:
            pnl_pct = (current_price - buy_price) / buy_price
        else:
            pnl_pct = 0
        
        # Check exit conditions
        should_sell = False
        reason = ""
        
        # Take profit: +80%
        if pnl_pct >= CONFIG["take_profit"]:
            should_sell = True
            reason = f"Take profit (+{pnl_pct:.0%})"
        # Stop loss: -30%
        elif pnl_pct <= -CONFIG["stop_loss"]:
            should_sell = True
            reason = f"Stop loss ({pnl_pct:.0%})"
        
        if should_sell:
            exit_signals.append({
                "market_id": market_id,
                "bucket": trade["bucket"],
                "buy_price": buy_price,
                "current_price": current_price,
                "pnl_pct": pnl_pct,
                "reason": reason,
                "shares": trade["shares"],
                "amount": trade["amount"]
            })
    
    return exit_signals

def format_exit_report(exit_signals):
    """Format exit signals for notification"""
    if not exit_signals:
        return None
    
    msg = "🚨 **AUTO-SELL SIGNALS**\n\n"
    
    for sig in exit_signals:
        emoji = "🟢" if sig["pnl_pct"] > 0 else "🔴"
        msg += f"**{sig['bucket']}**\n"
        msg += f"  买入: {sig['buy_price']:.1%} → 当前: {sig['current_price']:.1%}\n"
        msg += f"  {emoji} P/L: {sig['pnl_pct']:+.0%}\n"
        msg += f"  原因: {sig['reason']}\n\n"
    
    return msg

if __name__ == "__main__":
    print("=== Simmer Monitor with Auto-Sell ===")
    print()
    
    # Check for exit signals
    print("🔍 Checking exit signals...")
    exit_signals = check_exit_signals()
    
    if exit_signals:
        print(format_exit_report(exit_signals))
    else:
        print("✅ No exit signals - holding positions")
