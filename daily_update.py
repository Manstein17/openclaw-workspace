#!/usr/bin/env python3
"""
A股数据更新 - 按API速率优化
- 腾讯实时: 0.1秒/只
- 新浪历史: 0.3秒/只
- 每日增量更新
"""
import requests
import pandas as pd
import os
import time
import random
from datetime import datetime
import glob
import sys

# 配置
CACHE_DIR = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"
REQUEST_DELAY = 0.7  # 新浪历史接口安全间隔

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

session = requests.Session()
session.trust_env = False

def get_sina_kline(symbol, days=10):
    """新浪获取K线"""
    code = f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}'
    url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    
    for attempt in range(3):
        try:
            r = session.get(url, params={
                'symbol': code,
                'scale': '240',
                'ma': '5,10,20',
                'datalen': str(days)
            }, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    return data
        except:
            pass
        time.sleep(0.5)
    
    return None

def need_update(symbol):
    """检查是否需要更新"""
    file_path = f"{CACHE_DIR}/{symbol}.csv"
    
    if not os.path.exists(file_path):
        return True
    
    try:
        df = pd.read_csv(file_path)
        if len(df) > 0:
            last_date = str(df.iloc[-1]['日期'])
            # 今日或昨日无需更新
            if '2026-02-25' in last_date or '2026-02-24' in last_date:
                return False
    except:
        pass
    
    return True

def update_stock(symbol):
    """更新单只股票"""
    if not need_update(symbol):
        return True, "已是最新"
    
    data = get_sina_kline(symbol, days=15)
    
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
            
            file_path = f"{CACHE_DIR}/{symbol}.csv"
            
            if os.path.exists(file_path):
                df_old = pd.read_csv(file_path)
                combined = pd.concat([df_old, df_new], ignore_index=True)
                combined = combined.drop_duplicates(subset=['日期'], keep='last')
                combined = combined.sort_values('日期')
                combined.to_csv(file_path, index=False)
            else:
                df_new.to_csv(file_path, index=False)
            
            return True, f"+{len(data)}条"
        except Exception as e:
            pass
    
    return False, "失败"

def main():
    print(f"\n{'='*50}")
    print(f"A股数据更新 (速率优化版)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"间隔: {REQUEST_DELAY}秒/只")
    print(f"{'='*50}\n")
    
    # 获取所有股票
    files = glob.glob(f"{CACHE_DIR}/*.csv")
    all_symbols = [os.path.basename(f).replace('.csv', '') for f in files]
    
    # 需要更新的
    need_list = [s for s in all_symbols if need_update(s)]
    
    print(f"总股票: {len(all_symbols)}")
    print(f"需更新: {len(need_list)}")
    
    if not need_list:
        print("\n全部已是最新!")
        return
    
    # 随机顺序
    random.shuffle(need_list)
    
    success = 0
    fail = 0
    start_time = time.time()
    
    print(f"\n开始更新...\n")
    
    for i, symbol in enumerate(need_list):
        ok, msg = update_stock(symbol)
        
        if ok:
            success += 1
        else:
            fail += 1
        
        # 进度
        if (i + 1) % 100 == 0:
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed
            remaining = len(need_list) - i - 1
            mins = remaining / rate / 60
            print(f"进度: {i+1}/{len(need_list)} | 成功:{success} | 预计剩余:{mins:.1f}分钟")
        
        time.sleep(REQUEST_DELAY)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'='*50}")
    print(f"完成!")
    print(f"耗时: {elapsed/60:.1f}分钟")
    print(f"成功: {success}")
    print(f"失败: {fail}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
