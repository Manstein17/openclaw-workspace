#!/usr/bin/env python3
"""
持仓股实时更新 - 快速版
只更新持仓股，绕过代理
"""
import os
import sys
import time

# 强制不使用代理
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['NO_PROXY'] = '*'

CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_cache/daily")

# 持仓
POSITIONS = {
    '300861': {'shares': 1073, 'avg': 18.63, 'name': '美畅股份'},
    '300719': {'shares': 766, 'avg': 20.89, 'name': '安达维尔'},
    '300678': {'shares': 376, 'avg': 34.01, 'name': '中科信息'},
    '300875': {'shares': 235, 'avg': 43.46, 'name': '捷强装备'},
    '000428': {'shares': 2108, 'avg': 3.89, 'name': '华天酒店'}
}

def get_realtime_price(symbol):
    """直接用curl获取实时价格"""
    import subprocess
    
    # 判断市场
    if symbol.startswith('300') or symbol.startswith('688'):
        secid = f'1.{symbol}'  # 创业板
    else:
        secid = f'0.{symbol}'  # 上海/深圳
    
    url = f'http://push2.eastmoney.com/api/qt/stock/get?fltt=2&fields=f43,f58,f170,f171&secid={secid}'
    
    try:
        result = subprocess.run(
            ['curl', '-s', '--noproxy', '*', url],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        import json
        data = json.loads(result.stdout)
        if data.get('data'):
            d = data['data']
            price = d.get('f43', 0) / 100
            name = d.get('f58', '')
            pct = d.get('f170', 0) / 100
            return price, pct, name
    except Exception as e:
        print(f"错误: {e}")
    
    return None, None, None

def main():
    print("\n=== 持仓实时价格 ===\n")
    
    total_pnl = 0
    
    for symbol, info in POSITIONS.items():
        price, pct, name = get_realtime_price(symbol)
        
        if price:
            shares = info['shares']
            avg = info['avg']
            pnl = (price - avg) * shares
            pnl_pct = (price - avg) / avg * 100
            total_pnl += pnl
            
            print(f"{symbol} {name}")
            print(f"  现价: ¥{price:.2f} ({pct:+.2f}%)")
            print(f"  成本: ¥{avg:.2f}")
            print(f"  股数: {shares}")
            print(f"  盈亏: ¥{pnl:+,.0f} ({pnl_pct:+.1f}%)")
            print()
        else:
            print(f"{symbol} {info['name']}: 获取失败\n")
    
    print(f"{'='*30}")
    print(f"总盈亏: ¥{total_pnl:+,.0f}")
    print(f"{'='*30}")

if __name__ == "__main__":
    main()
