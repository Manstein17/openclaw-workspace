#!/usr/bin/env python3
"""
智能数据更新策略
- 交易时段增量更新持仓股
- 非交易时段批量更新
- 多源备份
"""
import requests
import pandas as pd
import os
import time
import json
import random
from datetime import datetime, timedelta
import glob
import sys

CACHE_DIR = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

session = requests.Session()
session.trust_env = False

def is_market_hours():
    """是否交易时段"""
    now = datetime.now()
    hour = now.hour
    weekday = now.weekday()
    
    if weekday >= 5:  # 周末
        return False
    
    # 9:30-11:30, 13:00-15:00
    if (9 <= hour < 11) or (13 <= hour < 15):
        return True
    return False

def get_sina_kline(symbol, days=5):
    """新浪K线"""
    code = f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}'
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    
    try:
        r = session.get(url, params={'symbol': code, 'scale': '240', 'datalen': str(days)}, timeout=8)
        data = r.json()
        if isinstance(data, list) and len(data) > 0:
            return data
    except:
        pass
    return None

def update_stock(symbol):
    """更新单只"""
    file_path = f"{CACHE_DIR}/{symbol}.csv"
    
    # 检查是否需要更新
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if len(df) > 0 and '2026-02-25' in str(df.iloc[-1]['日期']):
                return True, "已是最新"
        except:
            pass
    
    data = get_sina_kline(symbol, days=10)
    if data:
        try:
            df_new = pd.DataFrame(data)
            df_new = df_new.rename(columns={
                'day': '日期', 'open': '开盘', 'close': '收盘',
                'high': '最高', 'low': '最低', 'volume': '成交量'
            })
            for col in ['开盘', '收盘', '最高', '最低', '成交量']:
                df_new[col] = pd.to_numeric(df_new[col], errors='coerce')
            df_new['股票代码'] = symbol
            
            if os.path.exists(file_path):
                df_old = pd.read_csv(file_path)
                combined = pd.concat([df_old, df_new], ignore_index=True)
                combined = combined.drop_duplicates(subset=['日期'], keep='last')
                combined = combined.sort_values('日期')
                combined.to_csv(file_path, index=False)
            else:
                df_new.to_csv(file_path, index=False)
            
            return True, f"+{len(data)}条"
        except:
            pass
    
    return False, "失败"

def smart_update():
    """智能更新"""
    # 持仓股优先
    positions = ['300861', '300719', '300678', '300875', '000428']
    
    print(f"=== 智能数据更新 ===")
    print(f"时间: {datetime.now().strftime('%H:%M')}")
    print(f"交易时段: {'是' if is_market_hours() else '否'}")
    print()
    
    # 1. 先更新持仓股
    print("【持仓股更新】")
    for s in positions:
        ok, msg = update_stock(s)
        print(f"  {s}: {'✅' if ok else '❌'} {msg}")
        time.sleep(0.3)
    
    # 2. 如果非交易时段，更新更多
    if not is_market_hours():
        print("\n【批量更新】")
        
        # 获取所有股票，随机选200只
        files = glob.glob(f"{CACHE_DIR}/*.csv")
        all_symbols = [os.path.basename(f).replace('.csv', '') for f in files]
        
        # 排除已更新的
        need_update = []
        for s in all_symbols:
            if s not in positions:
                f = f"{CACHE_DIR}/{s}.csv"
                try:
                    df = pd.read_csv(f)
                    if len(df) > 0 and '2026-02-25' not in str(df.iloc[-1]['日期']):
                        need_update.append(s)
                except:
                    need_update.append(s)
        
        # 随机选200只
        random.shuffle(need_update)
        batch = need_update[:200]
        
        success = 0
        for i, s in enumerate(batch):
            ok, _ = update_stock(s)
            if ok:
                success += 1
            
            if (i + 1) % 50 == 0:
                print(f"  进度: {i+1}/{len(batch)} 成功:{success}")
            
            time.sleep(0.2)
        
        print(f"  完成: 成功{success}/{len(batch)}")
    
    # 3. 统计
    print("\n【统计】")
    files = glob.glob(f"{CACHE_DIR}/*.csv")
    today = 0
    for f in files[:1000]:
        try:
            df = pd.read_csv(f)
            if len(df) > 0 and '2026-02-25' in str(df.iloc[-1]['日期']):
                today += 1
        except:
            pass
    print(f"  今日更新: {today}/1000")
    print(f"  总股票: {len(files)}")

if __name__ == "__main__":
    smart_update()
