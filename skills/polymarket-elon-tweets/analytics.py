#!/usr/bin/env python3
"""
Elon Tweet Trading Analytics
历史交易分析、周报/月报生成
"""
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

TRADES_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_trades.json")

def load_trades():
    """加载所有交易"""
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, "r") as f:
            return json.load(f)
    return []

def filter_by_period(trades, days=None, start_date=None, end_date=None):
    """按时间周期筛选交易"""
    filtered = []
    now = datetime.now()
    
    for trade in trades:
        try:
            trade_time = datetime.fromisoformat(trade["timestamp"])
        except:
            continue
        
        if days:
            cutoff = now - timedelta(days=days)
            if trade_time >= cutoff:
                filtered.append(trade)
        elif start_date:
            start = datetime.fromisoformat(start_date) if isinstance(start_date, str) else start_date
            end = datetime.fromisoformat(end_date) if end_date and isinstance(end_date, str) else now
            if start <= trade_time <= end:
                filtered.append(trade)
        else:
            filtered.append(trade)
    
    return filtered

def analyze_period(trades, period_name):
    """分析指定周期的交易"""
    stats = {
        "period": period_name,
        "total_trades": 0,
        "buy_trades": 0,
        "sell_trades": 0,
        "dry_run_trades": 0,
        "live_trades": 0,
        "total_invested": 0,
        "unique_markets": set(),
        "buckets_traded": defaultdict(int),
        "by_market": defaultdict(lambda: {"buys": 0, "sells": 0, "invested": 0}),
    }
    
    for trade in trades:
        stats["total_trades"] += 1
        
        # 模式统计
        if trade.get("mode") == "dry_run":
            stats["dry_run_trades"] += 1
        else:
            stats["live_trades"] += 1
        
        # 动作统计
        if trade.get("action") == "buy":
            stats["buy_trades"] += 1
            stats["total_invested"] += trade.get("amount_usd", 0)
            
            market = trade.get("market_question", "Unknown")[:50]
            stats["unique_markets"].add(market)
            stats["by_market"][market]["buys"] += 1
            stats["by_market"][market]["invested"] += trade.get("amount_usd", 0)
            
            bucket = trade.get("bucket", "unknown")
            stats["buckets_traded"][bucket] += 1
            
        elif trade.get("action") == "sell":
            stats["sell_trades"] += 1
            market = trade.get("market_question", "Unknown")[:50]
            stats["by_market"][market]["sells"] += 1
    
    # 转换set为数量
    stats["unique_markets"] = len(stats["unique_markets"])
    stats["buckets_traded"] = dict(stats["buckets_traded"])
    stats["by_market"] = dict(stats["by_market"])
    
    return stats

def calculate_win_rate(trades):
    """计算模拟胜率（基于dry run的预测）"""
    # 这需要结合市场价格变化来计算，暂时返回基本信息
    wins = 0
    total = 0
    
    for trade in trades:
        if trade.get("mode") == "dry_run" and trade.get("action") == "buy":
            # 简单计算：如果买入后价格翻倍算win
            price = trade.get("price", 0)
            if price > 0 and price < 0.5:  # 低价买入
                total += 1
                # 这里需要结合实际价格变化，暂时不计算
    
    return {"estimated": None, "note": "需要结合实际平仓数据计算"}

def generate_summary(trades):
    """生成汇总统计"""
    if not trades:
        return {"error": "No trades found"}
    
    # 按时间分组
    now = datetime.now()
    today = now.date()
    
    today_trades = [t for t in trades if datetime.fromisoformat(t["timestamp"]).date() == today]
    week_trades = filter_by_period(trades, days=7)
    month_trades = filter_by_period(trades, days=30)
    all_trades = trades
    
    return {
        "generated_at": now.isoformat(),
        "today": {
            "trades": len(today_trades),
            "invested": sum(t.get("amount_usd", 0) for t in today_trades if t.get("action") == "buy"),
        },
        "last_7_days": analyze_period(week_trades, "Last 7 days"),
        "last_30_days": analyze_period(month_trades, "Last 30 days"),
        "all_time": analyze_period(all_trades, "All time"),
    }

def print_report():
    """打印分析报告"""
    trades = load_trades()
    
    if not trades:
        print("暂无交易记录")
        return
    
    summary = generate_summary(trades)
    
    print("=" * 60)
    print("📈 Elon Tweet 交易分析报告")
    print("=" * 60)
    print(f"生成时间: {summary['generated_at']}")
    print()
    
    # 今日
    print("📅 今日")
    print(f"   交易笔数: {summary['today']['trades']}")
    print(f"   投入金额: ${summary['today']['invested']:.2f}")
    print()
    
    # 本周
    print("📆 本周 (Last 7 days)")
    w = summary["last_7_days"]
    print(f"   总交易: {w['total_trades']} (实盘: {w['live_trades']}, 模拟: {w['dry_run_trades']})")
    print(f"   买入: {w['buy_trades']}, 卖出: {w['sell_trades']}")
    print(f"   投入总额: ${w['total_invested']:.2f}")
    print(f"   涉及市场: {w['unique_markets']}")
    if w["buckets_traded"]:
        print(f"   交易桶区间: {', '.join(w['buckets_traded'].keys())}")
    print()
    
    # 本月
    print("📆 本月 (Last 30 days)")
    m = summary["last_30_days"]
    print(f"   总交易: {m['total_trades']} (实盘: {m['live_trades']}, 模拟: {m['dry_run_trades']})")
    print(f"   买入: {m['buy_trades']}, 卖出: {m['sell_trades']}")
    print(f"   投入总额: ${m['total_invested']:.2f}")
    print()
    
    # 全部
    print("📆 全部历史")
    a = summary["all_time"]
    print(f"   总交易: {a['total_trades']}")
    print(f"   实盘交易: {a['live_trades']}")
    print(f"   投入总额: ${a['total_invested']:.2f}")
    print(f"   涉及市场数: {a['unique_markets']}")
    print()
    
    # 按市场详情
    if a["by_market"]:
        print("🏪 按市场详情:")
        for market, data in a["by_market"].items():
            print(f"   • {market}")
            print(f"     买入: {data['buys']}, 卖出: {data['sells']}, 投入: ${data['invested']:.2f}")
    
    # 保存报告
    report_file = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_analytics.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\n📄 详细报告已保存: {report_file}")

if __name__ == "__main__":
    print_report()
