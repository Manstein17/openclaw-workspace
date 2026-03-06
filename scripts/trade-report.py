#!/usr/bin/env python3
"""
Quick trade report command
Usage: python3 trade-report.py
"""
import os
import json
from datetime import datetime

JOURNAL_FILE = os.path.expanduser("~/.openclaw/workspace/.trade-journal.json")

def get_report():
    if not os.path.exists(JOURNAL_FILE):
        return "📊 No trades recorded yet"
    
    with open(JOURNAL_FILE) as f:
        journal = json.load(f)
    
    stats = journal['stats']
    positions = journal.get('positions', {})
    
    # Get current prices
    try:
        import sys
        sys.path.insert(0, os.path.expanduser('~/.openclaw/workspace/skills/polymarket-elon-tweets'))
        from elon_tweets import import_event
        
        events = ["https://polymarket.com/event/elon-musk-of-tweets-february-27-march-6"]
        price_map = {}
        for event_url in events:
            try:
                result = import_event(event_url)
                if result and "markets" in result:
                    for m in result["markets"]:
                        price_map[m["market_id"]] = m.get("current_probability", 0)
            except:
                continue
    except:
        price_map = {}
    
    report = []
    report.append("=" * 40)
    report.append("📊 交易报告")
    report.append("=" * 40)
    report.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")
    report.append("📈 总体统计")
    report.append(f"  总交易笔数: {stats['total_trades']}")
    report.append(f"  盈利笔数: {stats['winning_trades']}")
    report.append(f"  总盈亏: ${stats['total_pnl']:.2f}")
    report.append("")
    
    if positions:
        report.append("📊 当前持仓")
        total_unrealized = 0
        for mid, trade in positions.items():
            current = price_map.get(mid, trade.get('current_price', trade['price']))
            value = trade['shares'] * current
            pnl = value - trade['amount']
            total_unrealized += pnl
            emoji = "🟢" if pnl > 0 else "🔴"
            report.append(f"  {trade['bucket']} ({trade['event']})")
            report.append(f"    买入: {trade['price']:.1%} → 当前: {current:.1%}")
            report.append(f"    成本: ${trade['amount']:.2f} → 价值: ${value:.2f}")
            report.append(f"    {emoji} 盈亏: ${pnl:.2f}")
        report.append(f"  📊 未实现盈亏: ${total_unrealized:.2f}")
    else:
        report.append("📊 无持仓")
    
    report.append("")
    report.append("📌 参考")
    report.append("  Simmer 胜率: 74.4%")
    report.append("  算法优化: 每3天")
    report.append("=" * 40)
    
    return "\n".join(report)

if __name__ == "__main__":
    print(get_report())
