#!/usr/bin/env python3
"""
Mert Sniper v2 - 基于 Simmer 文档重写

改进点:
1. 使用 /briefing 端点扫描机会
2. 使用 opportunity_score 筛选
3. 使用 /context 端点获取深度分析
4. 检查滑点 (slippage)
5. 使用 edge 分析
6. 防止 flip-flop

Usage:
    python mert_sniper_v2.py              # Dry run
    python mert_sniper_v2.py --live       # Execute real trades
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

sys.stdout.reconfigure(line_buffering=True)

# =============================================================================
# Configuration
# =============================================================================

API_KEY = os.environ.get("SIMMER_API_KEY", "sk_live_XXXXX_REDACTED")
SIMMER_API = "https://api.simmer.markets"

# 交易参数
MIN_OPPORTUNITY_SCORE = 0   # 降低门槛，有分数或符合分裂条件就行
MIN_EDGE = 0.03           # 最小优势 3%
MAX_SLIPPAGE = 10.0        # 最大滑点 10% (放宽)
MIN_SPLIT = 0.35          # 最小分裂 35% (从40%降低)
MAX_SPLIT = 0.75          # 最大分裂 75% (从70%提高)
MAX_BET_USD = 5.0         # 最大投注
EXPIRY_WINDOW = 30         # 30分钟内过期 (从3分钟扩大)
MAX_TRADES_PER_RUN = 3    # 每次最多3笔

# Rate limiting - 避免请求过快被限
REQUEST_DELAY = 1.5  # 每次API请求间隔1.5秒

import time

# =============================================================================
# API Helpers
# =============================================================================

def sdk_request(method, endpoint, data=None):
    """Make API request to Simmer."""
    time.sleep(REQUEST_DELAY)  # Rate limiting
    
    url = f"{SIMMER_API}{endpoint}"
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
        print(f"  HTTP Error: {e.code} - {e.read().decode()}")
        return {"error": str(e)}
    except URLError as e:
        print(f"  URL Error: {e.reason}")
        return {"error": str(e)}

def get_briefing():
    """获取市场简报 - 一次调用获取所有机会"""
    return sdk_request("GET", "/api/sdk/briefing")

def get_market_context(market_id, my_probability=None):
    """获取单个市场的深度信息"""
    endpoint = f"/api/sdk/context/{market_id}"
    if my_probability:
        endpoint += f"?my_probability={my_probability}"
    return sdk_request("GET", endpoint)

def get_markets(status="active", limit=50):
    """获取市场列表"""
    return sdk_request("GET", f"/api/sdk/markets?status={status}&limit={limit}")

def get_portfolio():
    """获取投资组合"""
    return sdk_request("GET", "/api/sdk/portfolio")

def execute_trade(market_id, side, amount, venue, reasoning=""):
    """执行交易"""
    return sdk_request("POST", "/api/sdk/trade", {
        "market_id": market_id,
        "side": side,
        "amount": amount,
        "venue": venue,
        "reasoning": reasoning
    })

# =============================================================================
# 交易逻辑
# =============================================================================

def format_duration(minutes):
    """格式化时间"""
    if minutes < 1:
        return f"{int(minutes * 60)}s"
    elif minutes < 60:
        return f"{int(minutes)}m"
    else:
        return f"{int(minutes / 60)}h"

def analyze_opportunity(market, now):
    """分析市场机会"""
    question = market.get("question", "")
    current_prob = market.get("current_probability", 0.5)
    opp_score = market.get("opportunity_score", 0)
    resolves_at = market.get("resolves_at")
    
    # 计算剩余时间
    if resolves_at:
        try:
            end_time = datetime.fromisoformat(resolves_at.replace("Z", "+00:00"))
            minutes_left = (end_time - now).total_seconds() / 60
        except:
            minutes_left = 999
    else:
        minutes_left = 999
    
    return {
        "id": market.get("id"),
        "question": question,
        "current_prob": current_prob,
        "opportunity_score": opp_score,
        "minutes_left": minutes_left,
        "volume_24h": market.get("volume_24h", 0),
        "is_paid": market.get("is_paid", False),
        "tags": market.get("tags", [])
    }

def should_trade(opp, context):
    """基于上下文判断是否应该交易"""
    reasons = []
    
    # 1. 检查滑点
    slippage = context.get("slippage", {})
    estimates = slippage.get("estimates", [])
    if estimates:
        slippage_pct = estimates[0].get("slippage_pct", 0)
        if slippage_pct > MAX_SLIPPAGE:
            reasons.append(f"滑点过高: {slippage_pct:.1f}%")
    
    # 2. 检查 discipline (防止flip-flop)
    discipline = context.get("discipline", {})
    warning = discipline.get("flip_flop_warning")
    if warning:
        reasons.append(f"Flip-flop警告: {warning}")
    
    # 3. 检查 edge
    edge = context.get("edge", {})
    user_edge = edge.get("user_edge", 0)
    recommendation = edge.get("recommendation", "HOLD")
    
    if recommendation == "HOLD":
        reasons.append(f"Edge分析建议 HOLD")
    
    if user_edge < MIN_EDGE:
        reasons.append(f"优势不足: {user_edge*100:.1f}% < {MIN_EDGE*100:.1f}%")
    
    # 4. 检查是否已持仓
    position = context.get("position", {})
    if position.get("has_position"):
        reasons.append("已有持仓")
    
    should = len(reasons) == 0 and recommendation == "TRADE"
    return should, reasons

def scan_and_trade(live=False, venue="simmer"):
    """扫描市场并交易"""
    print("\n" + "=" * 60)
    print(f"🎯 Mert Sniper v2 - Simmer 文档优化版")
    print(f"   模式: {'🔴 实盘' if live else '🟡 模拟'}")
    print(f"   平台: {venue}")
    print("=" * 60)
    
    # 1. 获取市场列表 - 按机会分数排序
    print("\n📊 扫描市场...")
    markets = get_markets(status="active", limit=100)
    if "error" in markets:
        print(f"  ❌ 获取市场失败: {markets['error']}")
        return
    
    all_markets = markets.get("markets", [])
    print(f"  发现 {len(all_markets)} 个活跃市场")
    
    now = datetime.now(timezone.utc)
    
    # 2. 筛选符合条件的机会
    valid_opps = []
    for market in all_markets:
        # 获取基本信息
        question = market.get("question", "")
        current_prob = market.get("current_probability", 0.5)
        opp_score = market.get("opportunity_score", 0)
        resolves_at = market.get("resolves_at")
        
        # 过滤: 只看有分数的
        if opp_score < MIN_OPPORTUNITY_SCORE:
            continue
        
        # 计算剩余时间
        if resolves_at:
            try:
                end_time = datetime.fromisoformat(resolves_at.replace("Z", "+00:00"))
                minutes_left = (end_time - now).total_seconds() / 60
            except:
                continue
        else:
            continue
        
        # 过滤: 只看3分钟内的
        if minutes_left > EXPIRY_WINDOW or minutes_left < 0:
            continue
        
        # 过滤: 价格分裂
        if current_prob < MIN_SPLIT or current_prob > MAX_SPLIT:
            continue
        
        valid_opps.append({
            "id": market.get("id"),
            "question": question,
            "current_prob": current_prob,
            "opportunity_score": opp_score,
            "minutes_left": minutes_left,
            "volume_24h": market.get("volume_24h", 0),
            "is_paid": market.get("is_paid", False),
        })
    
    # 按机会分数排序
    valid_opps.sort(key=lambda x: x["opportunity_score"], reverse=True)
    print(f"  符合条件: {len(valid_opps)} 个")
    
    if not valid_opps:
        print("\n  ❌ 无符合条件的机会")
        return
    
    # 3. 获取深度分析并交易
    trades_done = 0
    for opp in valid_opps[:MAX_TRADES_PER_RUN]:
        market_id = opp["id"]
        question = opp["question"][:50]
        current_price = opp["current_prob"]
        
        print(f"\n  📊 {question}...")
        print(f"     机会分数: {opp['opportunity_score']}")
        print(f"     价格: YES {current_price:.0%} / NO {1-current_price:.0%}")
        print(f"     剩余: {opp['minutes_left']:.0f}分钟")
        
        # 获取深度分析 (带我们的概率估计)
        my_prob = current_price + 0.10  # 假设我们有10%优势
        context = get_market_context(market_id, my_prob)
        if "error" in context:
            print(f"     ❌ 获取上下文失败")
            continue
        
        # 分析是否应该交易
        should, reasons = should_trade(opp, context)
        
        if not should:
            print(f"     ❌ 不交易: {'; '.join(reasons)}")
            continue
        
        # 确定方向
        side = "yes" if current_price >= 0.5 else "no"
        
        # 计算数量
        amount = MAX_BET_USD / current_price
        
        # 打印分析
        edge = context.get("edge", {})
        slippage = context.get("slippage", {})
        slippage_estimates = slippage.get("estimates", [])
        try:
            slippage_pct = slippage_estimates[0].get("slippage_pct", 0) if slippage_estimates else 0
        except (IndexError, TypeError):
            slippage_pct = 0
        
        print(f"     ✅ 优势: {edge.get('user_edge', 0)*100:.1f}%")
        print(f"     📉 滑点: {slippage_pct:.1f}%")
        print(f"     📝 建议: {edge.get('recommendation', 'N/A')}")
        
        # 执行交易
        if live:
            result = execute_trade(market_id, side, MAX_BET_USD, venue, 
                f"Mert Sniper v2: {edge.get('user_edge', 0)*100:.1f}% edge, {slippage_pct:.1f}% slippage")
            if "error" in result:
                print(f"     ❌ 交易失败: {result.get('error')}")
            else:
                shares = result.get("shares_bought", amount)
                print(f"     ✅ 买入 {shares:.2f} {side.upper()} @ ${current_price:.2f}")
                trades_done += 1
        else:
            print(f"     🟡 [Dry Run] 买入 {amount:.2f} {side.upper()} @ ${current_price:.2f}")
            trades_done += 1
    
    print(f"\n{'='*60}")
    print(f"  扫描: {len(all_markets)} 市场")
    print(f"  符合: {len(valid_opps)} 个")
    print(f"  交易: {trades_done} 笔")
    if not live:
        print(f"\n  [DRY RUN MODE]")

# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Mert Sniper v2")
    parser.add_argument("--live", action="store_true", help="Execute real trades")
    parser.add_argument("--venue", default="simmer", choices=["simmer", "polymarket"], help="Trading venue")
    args = parser.parse_args()
    
    scan_and_trade(live=args.live, venue=args.venue)

if __name__ == "__main__":
    main()
