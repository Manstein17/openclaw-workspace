#!/usr/bin/env python3
"""
A股全量数据下载脚本
支持断点续传，分批下载
"""
import akshare as ak
import pandas as pd
import os
import time
import json
from datetime import datetime

# 配置
CACHE_DIR = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"
BATCH_SIZE = 50  # 每批下载50只
DELAY = 2  # 每只股票间隔秒数（避免限流）
PROGRESS_FILE = "/tmp/stock_download_progress.json"

def get_stock_list():
    """获取A股股票列表"""
    print("获取股票列表...")
    df = ak.stock_info_a_code_name()
    # 过滤ST股票
    df = df[~df['name'].str.contains('ST|退')]
    return df

def download_stock_data(symbol, name):
    """下载单只股票历史数据"""
    try:
        # 尝试获取数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date="20230101", 
                                end_date=datetime.now().strftime("%Y%m%d"))
        
        if df is not None and len(df) > 100:
            # 保存数据
            df.to_csv(f"{CACHE_DIR}/{symbol}.csv", index=False)
            return True
    except Exception as e:
        pass
    return False

def load_progress():
    """加载下载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'downloaded': [], 'failed': [], 'total': 0}

def save_progress(progress):
    """保存下载进度"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    # 确保目录存在
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 获取股票列表
    stocks = get_stock_list()
    print(f"总共 {len(stocks)} 只股票待下载")
    
    # 加载进度
    progress = load_progress()
    progress['total'] = len(stocks)
    
    # 已下载的股票
    downloaded = set(progress['downloaded'])
    failed = set(progress['failed'])
    
    # 需要下载的股票
    to_download = [s for s in stocks['code'].tolist() 
                   if s not in downloaded and s not in failed]
    
    print(f"已下载: {len(downloaded)}, 失败: {len(failed)}, 待下载: {len(to_download)}")
    
    # 分批下载
    batch_num = 0
    for i in range(0, len(to_download), BATCH_SIZE):
        batch = to_download[i:i+BATCH_SIZE]
        batch_num += 1
        
        print(f"\n=== 下载批次 {batch_num} ({i+1}-{i+len(batch)}) ===")
        
        for j, symbol in enumerate(batch):
            if symbol in downloaded:
                continue
            
            name = stocks[stocks['code'] == symbol]['name'].values[0] if symbol in stocks['code'].values else ''
            
            print(f"  [{j+1}/{len(batch)}] {symbol} {name}...", end=" ")
            
            success = download_stock_data(symbol, name)
            
            if success:
                downloaded.add(symbol)
                progress['downloaded'].append(symbol)
                print("✓")
            else:
                failed.add(symbol)
                progress['failed'].append(symbol)
                print("✗")
            
            time.sleep(DELAY)
        
        # 保存进度
        save_progress(progress)
        
        print(f"批次完成，已下载 {len(downloaded)}/{len(stocks)}")
    
    print(f"\n=== 下载完成 ===")
    print(f"成功: {len(downloaded)}")
    print(f"失败: {len(failed)}")

if __name__ == "__main__":
    main()
