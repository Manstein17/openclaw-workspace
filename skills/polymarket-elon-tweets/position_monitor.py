#!/usr/bin/env python3
"""
Elon Tweet Position Monitor
每小时检查持仓，监控盈亏，提示卖出时机
"""
import os
import sys
import json
from pathlib import Path

TRADES_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_trades.json")
POSITIONS_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_positions.json")
SIGNALS_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_signals.json")

# 卖出策略配置
SELL_TARGETS = [
    {"price": 0.30, "action": "提示", "reason": "30% - 初步盈利"},
    {"price": 0.50, "action": "考虑卖出", "reason": "50% - 半仓获利"},
    {"price": 0.70, "action": "建议卖出", "reason": "70% - 大幅盈利"},
    {"price": 0.80, "action": "强制卖出", "reason": "80% - 止盈线"},
]

def load_trades():
    """加载交易记录"""
    if os.path.exists(TRADES_FILE):
        with open(TRADES_FILE, "r") as f:
            return json.load(f)
    return []

def load_positions():
    """加载当前持仓（从Polymarket API或手动更新）"""
    if os.path.exists(POSITIONS_FILE):
        with open(POSITIONS_FILE, "r") as f:
            return json.load(f)
    return []

def save_positions(positions):
    """保存持仓"""
    os.makedirs(os.path.dirname(POSITIONS_FILE), exist_ok=True)
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

def get_current_prices():
    """从信号文件或API获取当前价格"""
    # 优先从最新的信号文件获取
    if os.path.exists(SIGNALS_FILE):
        with open(SIGNALS_FILE, "r") as f:
            signals = json.load(f)
            if signals and "buckets" in signals[0]:
                prices = {}
                for b in signals[0]["buckets"]:
                    prices[b["bucket"]] = b["price"]
                return prices
    return {}

def calculate_pnl(trades, current_prices):
    """计算持仓盈亏"""
    pnl_summary = {
        "total_invested": 0,
        "current_value": 0,
        "positions": [],
    }
    
    # 按bucket分组计算
    position_map = {}
    for trade in trades:
        if trade.get("mode") == "live" and trade.get("action") == "buy":
            bucket = trade.get("bucket")
            if bucket not in position_map:
                position_map[bucket] = {
                    "bucket": bucket,
                    "shares": 0,
                    "cost": 0,
                    "cost_per_share": 0,
                }
            position_map[bucket]["shares"] += trade.get("shares", 0)
            position_map[bucket]["cost"] += trade.get("amount_usd", 0)
    
    # 计算每个持仓的当前价值
    for bucket, pos in position_map.items():
        if pos["shares"] > 0:
            current_price = current_prices.get(bucket, 0)
            current_value = pos["shares"] * current_price
            pos["current_price"] = current_price
            pos["current_value"] = current_value
            pos["unrealized_pnl"] = current_value - pos["cost"]
            pos["pnl_percent"] = (pos["unrealized_pnl"] / pos["cost"] * 100) if pos["cost"] > 0 else 0
            
            pnl_summary["total_invested"] += pos["cost"]
            pnl_summary["current_value"] += current_value
            pnl_summary["positions"].append(pos)
    
    pnl_summary["total_pnl"] = pnl_summary["current_value"] - pnl_summary["total_invested"]
    pnl_summary["total_pnl_percent"] = (pnl_summary["total_pnl"] / pnl_summary["total_invested"] * 100) if pnl_summary["total_invested"] > 0 else 0
    
    return pnl_summary

def check_sell_signals(pnl_summary):
    """检查是否触发卖出信号"""
    alerts = []
    for pos in pnl_summary.get("positions", []):
        current_price = pos.get("current_price", 0)
        if current_price == 0:
            continue
            
        for target in SELL_TARGETS:
            if current_price >= target["price"]:
                alerts.append({
                    "bucket": pos["bucket"],
                    "current_price": current_price,
                    "target": target,
                    "shares": pos["shares"],
                    "potential_value": pos["shares"] * current_price,
                })
    return alerts

def generate_report():
    """生成持仓报告"""
    trades = load_trades()
    current_prices = get_current_prices()
    pnl_summary = calculate_pnl(trades, current_prices)
    sell_signals = check_sell_signals(pnl_summary)
    
    report = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "positions": pnl_summary["positions"],
        "total_invested": round(pnl_summary["total_invested"], 2),
        "current_value": round(pnl_summary["current_value"], 2),
        "total_pnl": round(pnl_summary["total_pnl"], 2),
        "total_pnl_percent": round(pnl_summary["total_pnl_percent"], 2),
        "sell_signals": sell_signals,
    }
    
    return report

def print_report():
    """打印报告"""
    report = generate_report()
    
    print("=" * 50)
    print("📊 Elon Tweet 持仓报告")
    print("=" * 50)
    print(f"更新时间: {report['timestamp']}")
    print()
    
    if not report["positions"]:
        print("暂无持仓")
        return
    
    print("📍 当前持仓:")
    print("-" * 50)
    print(f"{'桶区间':<12} {'股数':<8} {'成本':<8} {'当前价':<8} {'价值':<8} {'盈亏':<10}")
    print("-" * 50)
    
    for pos in report["positions"]:
        print(f"{pos['bucket']:<12} {pos['shares']:<8.2f} ${pos['cost']:<7.2f} ${pos.get('current_price', 0):<7.2f} ${pos['current_value']:<7.2f} ${pos['unrealized_pnl']:<+8.2f} ({pos['pnl_percent']:+.1f}%)")
    
    print("-" * 50)
    print(f"{'总计':<12} {'':<8} ${report['total_invested']:<7.2f} {'':<8} ${report['current_value']:<7.2f} ${report['total_pnl']:<+8.2f} ({report['total_pnl_percent']:+.1f}%)")
    print()
    
    if report["sell_signals"]:
        print("🚨 卖出信号:")
        for signal in report["sell_signals"]:
            print(f"   • 桶 {signal['bucket']}: 当前 {signal['current_price']:.1%} → 触发 {signal['target']['action']} ({signal['target']['reason']})")
    else:
        print("⏳ 暂无卖出信号")
    
    # 保存报告
    report_file = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_position_report.json")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n📄 报告已保存: {report_file}")

if __name__ == "__main__":
    print_report()
