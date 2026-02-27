#!/usr/bin/env python3
"""
补充下载失败股票 - 只要有数据就下载
"""
import akshare as ak
import os
from datetime import datetime
import time
import json

CACHE_DIR = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"
PROGRESS_FILE = "/tmp/stock_download_progress.json"
START_DATE = "20210101"
END_DATE = datetime.now().strftime("%Y%m%d")

def get_failed_stocks():
    """获取失败的股票列表"""
    # 读取成功的
    success = set()
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            data = json.load(f)
            success = set(data.get('downloaded', []))
    
    # 读取所有可能的股票
    import akshare as ak
    df = ak.stock_info_a_code_name()
    all_stocks = set(df['code'].tolist())
    
    # 差集 = 失败的
    failed = all_stocks - success
    return list(failed)

def download_one(symbol):
    """下载单只股票"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily", 
            start_date=START_DATE,
            end_date=END_DATE,
            adjust=""
        )
        
        # 只要有数据就保存（不限制天数）
        if df is not None and len(df) > 10:  # 放宽到10天
            df.to_csv(f"{CACHE_DIR}/{symbol}.csv", index=False)
            return True, len(df)
    except:
        pass
    return False, 0

def main():
    print("=== 补充下载失败股票 ===")
    print(f"时间范围: {START_DATE} - {END_DATE}")
    
    stocks = get_failed_stocks()
    print(f"待下载: {len(stocks)}只")
    
    success = 0
    for i, symbol in enumerate(stocks):
        if (i + 1) % 100 == 0:
            print(f"进度: {i+1}/{len(stocks)}")
        
        ok, days = download_one(symbol)
        if ok:
            success += 1
        
        time.sleep(0.3)  # 避免限流
    
    print(f"\n完成! 成功: {success}/{len(stocks)}")

if __name__ == "__main__":
    main()
