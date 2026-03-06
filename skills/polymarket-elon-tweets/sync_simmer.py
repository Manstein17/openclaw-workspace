#!/usr/bin/env python3
"""
Sync Simmer history trades to local journal
从 Simmer 获取历史模拟交易并记录到本地
"""
import os
import sys
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simmer_sdk import SimmerClient

# API Key
API_KEY = os.environ.get("SIMMER_API_KEY", "sk_live_REDACTED")

LOCAL_TRADES_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_trades.json")

def load_local_trades():
    """加载本地交易记录"""
    if os.path.exists(LOCAL_TRADES_FILE):
        with open(LOCAL_TRADES_FILE, "r") as f:
            return json.load(f)
    return []

def save_local_trades(trades):
    """保存本地交易记录"""
    os.makedirs(os.path.dirname(LOCAL_TRADES_FILE), exist_ok=True)
    with open(LOCAL_TRADES_FILE, "w") as f:
        json.dump(trades, f, indent=2)

def sync_from_simmer():
    """从 Simmer 同步交易到本地"""
    print("🔄 从 Simmer 同步交易数据...")
    
    client = SimmerClient(api_key=API_KEY)
    positions = client.get_positions()
    
    print(f"📊 Simmer 上发现 {len(positions)} 个持仓")
    
    # 加载本地记录
    local_trades = load_local_trades()
    
    # 获取已存在的 trade_id 避免重复
    existing_ids = set()
    for t in local_trades:
        if t.get("simmer_trade_id"):
            existing_ids.add(t["simmer_trade_id"])
    
    new_trades = []
    
    for pos in positions:
        # 解析 Position 对象
        market_id = pos.market_id
        question = pos.question
        shares = pos.shares_yes
        current_value = pos.current_value
        pnl = pos.pnl
        cost_basis = pos.cost_basis
        avg_cost = pos.avg_cost
        current_price = pos.current_price
        status = pos.status
        sources = pos.sources
        
        # 提取桶区间
        bucket = "unknown"
        if "tweets from" in question.lower():
            import re
            # 尝试提取数字区间，如 "220-239"
            match = re.search(r'(\d+)-(\d+)', question)
            if match:
                bucket = f"{match.group(1)}-{match.group(2)}"
        
        trade_id = f"simmer_{market_id[:8]}"
        
        # 跳过已存在的
        if trade_id in existing_ids:
            print(f"  ⏭️  跳过已存在: {bucket}")
            continue
        
        # 创建交易记录
        trade = {
            "timestamp": datetime.now().isoformat(),
            "source": "simmer_sync",
            "simmer_trade_id": trade_id,
            "market_id": market_id,
            "market_question": question[:100] if question else None,
            "bucket": bucket,
            "price": avg_cost,
            "amount_usd": cost_basis,
            "shares": shares,
            "action": "buy",
            "mode": "simmer_dry_run",  # Simmer 上的是模拟盘
            "current_price": current_price,
            "current_value": current_value,
            "pnl": pnl,
            "status": status,
            "sources": sources,
        }
        
        new_trades.append(trade)
        print(f"  ✅ 新增: {bucket} | {shares:.1f}股 @ ${avg_cost:.3f} | P&L: ${pnl:.2f}")
    
    # 合并并保存
    if new_trades:
        # 放在前面（最新的）
        local_trades = new_trades + local_trades
        save_local_trades(local_trades)
        print(f"\n✅ 已同步 {len(new_trades)} 笔交易到本地")
    else:
        print("\n⏭️  没有新交易需要同步")
    
    return local_trades

def show_summary():
    """显示汇总"""
    trades = load_local_trades()
    
    # 按来源分组
    sources = {}
    for t in trades:
        src = t.get("source", "unknown")
        if src not in sources:
            sources[src] = {"count": 0, "invested": 0, "pnl": 0}
        sources[src]["count"] += 1
        sources[src]["invested"] += t.get("amount_usd", 0)
        sources[src]["pnl"] += t.get("pnl", 0)
    
    print("\n" + "=" * 50)
    print("📈 交易汇总")
    print("=" * 50)
    
    for src, data in sources.items():
        print(f"\n🏷️  {src}:")
        print(f"   交易数: {data['count']}")
        print(f"   投入: ${data['invested']:.2f}")
        print(f"   P&L: ${data['pnl']:.2f}")
    
    # 总计
    total_invested = sum(t.get("amount_usd", 0) for t in trades)
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    print(f"\n💰 总计:")
    print(f"   交易数: {len(trades)}")
    print(f"   投入: ${total_invested:.2f}")
    print(f"   P&L: ${total_pnl:.2f}")

if __name__ == "__main__":
    sync_from_simmer()
    show_summary()
