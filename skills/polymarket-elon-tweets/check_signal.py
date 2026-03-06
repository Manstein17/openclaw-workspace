#!/usr/bin/env python3
"""
Elon Tweet Signal Monitor
每分钟检查一次，发现机会时保存到信号文件并通知
"""
import os
import sys
import json
from pathlib import Path

# 确保能导入 elon_tweets 的模块
sys.path.insert(0, str(Path(__file__).parent))

from elon_tweets import (
    get_xtracker_trackings,
    get_xtracker_stats,
    search_markets,
    import_event,
    match_tracking_to_event,
    find_target_buckets,
    evaluate_cluster,
    get_client,
    MAX_BUCKET_SUM,
    MAX_POSITION_USD,
    BUCKET_SPREAD,
)

SIGNAL_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_signals.json")

def check_opportunities():
    """检查是否有交易机会"""
    print("📡 Checking for Elon tweet trading opportunities...")
    
    # 获取 XTracker 数据
    trackings = get_xtracker_trackings()
    if not trackings:
        print("  ⚠️ No active trackings")
        return None
    
    # 获取统计
    tracking_stats = {}
    for t in trackings:
        stats = get_xtracker_stats(t["id"])
        if stats and stats.get("stats"):
            tracking_stats[t["id"]] = {
                "title": t.get("title", ""),
                "total": stats["stats"].get("total", 0),
                "pace": stats["stats"].get("pace", 0),
                "percent_complete": stats["stats"].get("percentComplete", 0),
                "days_remaining": stats["stats"].get("daysRemaining", 0),
            }
    
    # 搜索市场
    markets = search_markets("tweets")
    if not markets:
        print("  ⚠️ No markets found")
        return None
    
    # 按事件分组
    events = {}
    for m in markets:
        event_id = m.get("event_id") or m.get("event_ref")
        if not event_id:
            continue
        if event_id not in events:
            events[event_id] = {"name": m.get("event_name", ""), "markets": []}
        events[event_id]["markets"].append(m)
    
    opportunities = []
    
    for event_id, event_data in events.items():
        event_name = event_data["name"]
        event_markets = event_data["markets"]
        
        # 匹配 XTracker
        matched_stats = None
        for tid, stats in tracking_stats.items():
            if match_tracking_to_event(stats["title"], event_name):
                matched_stats = stats
                break
        
        if not matched_stats:
            continue
        
        projected_count = matched_stats["pace"]
        current_count = matched_stats["total"]
        
        # 跳过不可靠的预测
        if current_count == 0 and matched_stats["days_remaining"] > 2:
            continue
        
        # 找目标桶
        targets = find_target_buckets(event_markets, projected_count)
        if not targets:
            continue
        
        # 评估集群
        is_profitable, total_cost, expected_profit = evaluate_cluster(targets)
        
        if is_profitable:
            opportunity = {
                "timestamp": __import__("datetime").datetime.now().isoformat(),
                "event_name": event_name[:80],
                "current_count": current_count,
                "projected_count": projected_count,
                "percent_complete": matched_stats["percent_complete"],
                "days_remaining": matched_stats["days_remaining"],
                "buckets": [],
                "total_cost": total_cost,
                "expected_profit": expected_profit,
            }
            
            for bucket in targets:
                m = bucket["market"]
                opportunity["buckets"].append({
                    "market_id": m.get("market_id") or m.get("id"),
                    "question": m.get("question", "")[:100],
                    "bucket": f"{bucket['low']}-{bucket['high']}",
                    "price": bucket["price"],
                    "amount": MAX_POSITION_USD,
                })
            
            opportunities.append(opportunity)
    
    return opportunities

def save_signal(opportunities):
    """保存信号到文件"""
    os.makedirs(os.path.dirname(SIGNAL_FILE), exist_ok=True)
    with open(SIGNAL_FILE, "w") as f:
        json.dump(opportunities, f, indent=2)
    print(f"  💾 Signals saved to {SIGNAL_FILE}")

def main():
    print("🔍 Elon Tweet Signal Monitor")
    print("=" * 40)
    
    opportunities = check_opportunities()
    
    if opportunities:
        print(f"\n✅ Found {len(opportunities)} opportunity!")
        for opp in opportunities:
            print(f"\n🎯 {opp['event_name']}")
            print(f"   Current: {opp['current_count']} | Projected: {opp['projected_count']}")
            print(f"   Cluster cost: ${opp['total_cost']:.2f} | Expected profit: ${opp['expected_profit']:.2f}")
            for b in opp["buckets"]:
                print(f"   • {b['bucket']} @ ${b['price']:.2f}")
        
        save_signal(opportunities)
    else:
        print("  ⏸️ No opportunities right now")
        # 清空信号文件
        if os.path.exists(SIGNAL_FILE):
            os.remove(SIGNAL_FILE)

if __name__ == "__main__":
    main()
