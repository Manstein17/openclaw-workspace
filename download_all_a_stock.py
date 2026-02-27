#!/usr/bin/env python3
"""
A股全量数据下载 - 5年历史数据
支持断点续传，后台运行
"""
import akshare as ak
import pandas as pd
import os
import time
import json
from datetime import datetime
import sys

# 配置
CACHE_DIR = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"
BATCH_SIZE = 100  # 每批100只
DELAY = 0.5  # 每只间隔秒数
START_DATE = "20210101"  # 5年数据
END_DATE = datetime.now().strftime("%Y%m%d")
PROGRESS_FILE = "/tmp/stock_download_progress.json"
LOG_FILE = "/tmp/stock_download.log"

def log(msg):
    """日志记录"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(msg)

def get_stock_list():
    """获取A股股票列表"""
    log("获取股票列表...")
    df = ak.stock_info_a_code_name()
    # 过滤ST、退市、停牌
    df = df[~df['name'].str.contains('ST|退|停')]
    return df['code'].tolist()

def download_stock(symbol):
    """下载单只股票"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily", 
            start_date=START_DATE,
            end_date=END_DATE,
            adjust=""  # 不复权
        )
        
        if df is not None and len(df) > 800:  # 5年约1000个交易日
            df.to_csv(f"{CACHE_DIR}/{symbol}.csv", index=False)
            return True, len(df)
    except Exception as e:
        pass
    return False, 0

def load_progress():
    """加载下载进度"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {'downloaded': [], 'failed': [], 'total': 0}

def save_progress(progress):
    """保存进度"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    log("="*50)
    log("A股全量数据下载开始")
    log(f"目标: 5年历史数据 ({START_DATE} - {END_DATE})")
    log("="*50)
    
    # 获取股票列表
    stocks = get_stock_list()
    total = len(stocks)
    log(f"股票总数: {total}")
    
    # 加载进度
    progress = load_progress()
    progress['total'] = total
    
    downloaded = set(progress['downloaded'])
    failed = set(progress['failed'])
    
    # 需要下载的
    to_download = [s for s in stocks if s not in downloaded and s not in failed]
    log(f"已下载: {len(downloaded)}, 失败: {len(failed)}, 待下载: {len(to_download)}")
    
    success_count = len(downloaded)
    
    # 分批下载
    for i in range(0, len(to_download), BATCH_SIZE):
        batch = to_download[i:i+BATCH_SIZE]
        
        for j, symbol in enumerate(batch):
            if symbol in downloaded:
                continue
            
            success, rows = download_stock(symbol)
            
            if success:
                downloaded.add(symbol)
                progress['downloaded'].append(symbol)
                success_count += 1
            else:
                failed.add(symbol)
                progress['failed'].append(symbol)
            
            # 进度显示
            if (j + 1) % 10 == 0:
                log(f"进度: {success_count}/{total} ({success_count*100/total:.1f}%)")
            
            time.sleep(DELAY)
        
        # 保存进度
        save_progress(progress)
    
    log("="*50)
    log(f"下载完成!")
    log(f"成功: {len(downloaded)}")
    log(f"失败: {len(failed)}")
    log("="*50)

if __name__ == "__main__":
    main()
