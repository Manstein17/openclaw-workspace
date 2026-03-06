#!/usr/bin/env python3
"""
Trade Journal - Records real trades and analyzes performance
"""
import os
import json
from datetime import datetime
from pathlib import Path

JOURNAL_FILE = os.path.expanduser("~/.openclaw/workspace/.trade-journal.json")

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        with open(JOURNAL_FILE, 'r') as f:
            return json.load(f)
    return {
        "trades": [],
        "positions": {},
        "stats": {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0
        }
    }

def save_journal(journal):
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(journal, f, indent=2)

def record_trade(bucket, event, price, amount, shares, market_id, action="buy"):
    """Record a new trade"""
    journal = load_journal()
    
    trade = {
        "id": len(journal["trades"]) + 1,
        "timestamp": datetime.now().isoformat(),
        "bucket": bucket,
        "event": event,
        "price": price,
        "amount": amount,
        "shares": shares,
        "market_id": market_id,
        "action": action,
        "status": "open",
        "pnl": None,
        "close_price": None,
        "close_time": None
    }
    
    journal["trades"].append(trade)
    journal["positions"][market_id] = trade
    journal["stats"]["total_trades"] += 1
    
    save_journal(journal)
    return trade

def close_trade(market_id, close_price, pnl):
    """Close a position and record P&L"""
    journal = load_journal()
    
    if market_id in journal["positions"]:
        trade = journal["positions"][market_id]
        trade["status"] = "closed"
        trade["close_price"] = close_price
        trade["close_time"] = datetime.now().isoformat()
        trade["pnl"] = pnl
        
        journal["stats"]["total_pnl"] += pnl
        if pnl > 0:
            journal["stats"]["winning_trades"] += 1
        
        del journal["positions"][market_id]
        save_journal(journal)
        return trade
    return None

def update_position_prices(price_map):
    """Update current prices for open positions"""
    journal = load_journal()
    updated = []
    
    for market_id, current_price in price_map.items():
        if market_id in journal["positions"]:
            trade = journal["positions"][market_id]
            trade["current_price"] = current_price
            current_value = trade["shares"] * current_price
            trade["unrealized_pnl"] = current_value - trade["amount"]
            updated.append({
                "bucket": trade["bucket"],
                "price": current_price,
                "value": current_value,
                "pnl": trade["unrealized_pnl"]
            })
    
    if updated:
        save_journal(journal)
    return updated

def get_open_positions():
    """Get all open positions"""
    journal = load_journal()
    return journal["positions"]

def analyze_performance():
    """Analyze trade performance"""
    journal = load_journal()
    closed_trades = [t for t in journal["trades"] if t.get("status") == "closed"]
    
    if not closed_trades:
        return {
            "message": "No closed trades yet",
            "stats": journal["stats"],
            "open_positions": len(journal["positions"])
        }
    
    # Analyze by price range
    price_ranges = {
        "0-5%": [],
        "5-10%": [],
        "10-20%": [],
        "20%+": []
    }
    
    for t in closed_trades:
        price = t["price"]
        if price < 0.05:
            price_ranges["0-5%"].append(t)
        elif price < 0.10:
            price_ranges["5-10%"].append(t)
        elif price < 0.20:
            price_ranges["10-20%"].append(t)
        else:
            price_ranges["20%+"].append(t)
    
    analysis = {}
    for range_name, trades in price_ranges.items():
        if trades:
            wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
            total_pnl = sum(t.get("pnl", 0) for t in trades)
            analysis[range_name] = {
                "trades": len(trades),
                "wins": wins,
                "win_rate": wins / len(trades) * 100,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(trades) if trades else 0
            }
    
    # Find best range
    best_range = None
    if analysis:
        best = max(analysis.items(), key=lambda x: x[1].get("avg_pnl", 0))
        if best[1].get("avg_pnl", 0) > 0:
            best_range = best
    
    return {
        "total_closed": len(closed_trades),
        "total_open": len(journal["positions"]),
        "stats": journal["stats"],
        "by_price_range": analysis,
        "best_range": best_range,
        "worst_range": min(analysis.items(), key=lambda x: x[1].get("avg_pnl", 0)) if analysis else None
    }

def get_recommendations():
    """Get parameter recommendations based on actual performance"""
    analysis = analyze_performance()
    
    if not analysis.get("by_price_range"):
        return {
            "recommend_max_price": 0.20,
            "recommend_risk": 1.0,
            "reason": "No closed trades yet",
            "confidence": "low"
        }
    
    best = analysis.get("best_range")
    worst = analysis.get("worst_range")
    
    if best and best[1].get("avg_pnl", 0) > 0.3:
        # Very profitable range
        return {
            "recommend_max_price": 0.25,
            "recommend_risk": 0.9,
            "reason": f"Best range {best[0]} is very profitable",
            "confidence": "high"
        }
    elif best and best[1].get("avg_pnl", 0) > 0:
        # Profitable
        return {
            "recommend_max_price": 0.20,
            "recommend_risk": 1.0,
            "reason": f"Best range {best[0]} is profitable",
            "confidence": "medium"
        }
    elif worst and worst[1].get("avg_pnl", 0) < -0.3:
        # Losing money
        return {
            "recommend_max_price": 0.12,
            "recommend_risk": 1.3,
            "reason": f"Worst range {worst[0]} losing - tightening",
            "confidence": "medium"
        }
    else:
        return {
            "recommend_max_price": 0.15,
            "recommend_risk": 1.1,
            "reason": "Mixed results - staying cautious",
            "confidence": "low"
        }

def status():
    """Show current journal status"""
    journal = load_journal()
    analysis = analyze_performance()
    recommendations = get_recommendations()
    
    print("=== 📓 TRADE JOURNAL ===")
    print(f"Total trades: {journal['stats']['total_trades']}")
    print(f"Open positions: {len(journal['positions'])}")
    print(f"Closed trades: {analysis.get('total_closed', 0)}")
    print(f"Win rate: {journal['stats']['winning_trades']}/{analysis.get('total_closed', 1)}")
    print(f"Total PnL: ${journal['stats']['total_pnl']:.2f}")
    print()
    
    # Open positions
    if journal["positions"]:
        print("=== 📊 OPEN POSITIONS ===")
        total_unrealized = 0
        for mid, trade in journal["positions"].items():
            current = trade.get("current_price", trade["price"])
            value = trade["shares"] * current
            pnl = value - trade["amount"]
            total_unrealized += pnl
            emoji = "🟢" if pnl > 0 else "🔴"
            print(f"  {trade['bucket']}: {trade['price']:.1%} → {current:.1%} | {emoji} ${pnl:.2f}")
        print(f"  Unrealized PnL: ${total_unrealized:.2f}")
        print()
    
    if analysis.get("by_price_range"):
        print("=== 📈 PERFORMANCE BY PRICE RANGE ===")
        for range_name, data in analysis["by_price_range"].items():
            emoji = "🟢" if data["avg_pnl"] > 0 else "🔴"
            print(f"  {range_name}: {data['trades']} trades, {data['win_rate']:.0f}% win | {emoji} ${data['avg_pnl']:.2f} avg")
        print()
    
    print("=== 💡 RECOMMENDATIONS ===")
    print(f"  Max Price: {recommendations['recommend_max_price']:.0%}")
    print(f"  Risk: {recommendations['recommend_risk']}x")
    print(f"  Reason: {recommendations['reason']}")
    print(f"  Confidence: {recommendations['confidence']}")
    
    return recommendations

def auto_update_positions():
    """Automatically update position prices from Polymarket"""
    import sys
    sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/skills/polymarket-elon-tweets"))
    try:
        from elon_tweets import import_event
        
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
        
        if price_map:
            return update_position_prices(price_map)
    except:
        pass
    return []

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "status":
            status()
        elif cmd == "update":
            updated = auto_update_positions()
            if updated:
                print(f"Updated {len(updated)} positions")
                status()
            else:
                print("No positions to update")
        elif cmd == "record" and len(sys.argv) > 7:
            record_trade(sys.argv[2], sys.argv[3], float(sys.argv[4]), 
                        float(sys.argv[5]), float(sys.argv[6]), sys.argv[7])
        elif cmd == "close" and len(sys.argv) > 4:
            close_trade(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
        elif cmd == "analyze":
            result = analyze_performance()
            print(json.dumps(result, indent=2))
        elif cmd == "recommend":
            print(json.dumps(get_recommendations(), indent=2))
    else:
        status()
