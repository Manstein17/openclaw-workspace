#!/usr/bin/env python3
"""
并发数据更新脚本
- 多线程并发获取
- 分批处理，避免封禁
- 每批500只
"""
import os
import sys
import time
import random
import glob
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

# 配置
CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')
BATCH_SIZE = 500  # 每批500只
MAX_WORKERS = 3  # 并发数，降低以避免被封
REQUEST_DELAY = 1.5  # 每次请求间隔1.5秒

class BatchUpdater:
    """批量并发更新器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        self.updated = 0
        self.failed = 0
        self.lock = Lock()
    
    def get_stock_list(self):
        """获取需要更新的股票列表"""
        stocks = []
        
        for f in glob.glob(f'{CACHE_DIR}/*.csv'):
            try:
                symbol = os.path.basename(f).replace('.csv', '')
                df = pd.read_csv(f)
                if len(df) > 0:
                    last_date = str(df.iloc[-1]['日期'])[:10]
                    if last_date != '2026-02-27' and last_date != '2026-03-01':
                        stocks.append(symbol)
                else:
                    stocks.append(symbol)
            except:
                stocks.append(symbol)
        
        random.shuffle(stocks)
        return stocks[:BATCH_SIZE]
    
    def get_sina_kline(self, symbol, days=30):
        """获取新浪K线数据"""
        url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
        params = {
            'symbol': f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}',
            'scale': '240',
            'ma': 'no',
            'datalen': days
        }
        
        try:
            time.sleep(REQUEST_DELAY + random.uniform(0, 0.3))
            r = self.session.get(url, params=params, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                
                if data and isinstance(data, list):
                    records = []
                    for item in data:
                        records.append({
                            '日期': item.get('day', ''),
                            '股票代码': symbol,
                            '开盘': float(item.get('open', 0)),
                            '收盘': float(item.get('close', 0)),
                            '最高': float(item.get('high', 0)),
                            '最低': float(item.get('low', 0)),
                            '成交量': int(item.get('volume', 0)),
                        })
                    
                    if records:
                        return pd.DataFrame(records)
        except:
            pass
        
        return None
    
    def save_data(self, symbol, df):
        """保存数据"""
        path = f'{CACHE_DIR}/{symbol}.csv'
        df.to_csv(path, index=False)
    
    def update_stock(self, symbol):
        """更新单只股票"""
        df = self.get_sina_kline(symbol)
        
        with self.lock:
            if df is not None and len(df) > 0:
                self.save_data(symbol, df)
                self.updated += 1
                return f"✅ {symbol}"
            else:
                self.failed += 1
                return f"❌ {symbol}"
    
    def run(self):
        """运行批量更新"""
        print("=== 批量并发数据更新 ===")
        print(f"每批数量: {BATCH_SIZE}")
        print(f"并发数: {MAX_WORKERS}")
        print()
        
        stocks = self.get_stock_list()
        print(f"需要更新: {len(stocks)}只\n")
        
        start_time = time.time()
        
        # 并发执行
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self.update_stock, s): s for s in stocks}
            
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1
                
                if completed % 50 == 0:
                    print(f"📊 进度: {completed}/{len(stocks)} | 成功: {self.updated} | 失败: {self.failed}")
        
        elapsed = time.time() - start_time
        
        print(f"\n=== 完成 ===")
        print(f"成功: {self.updated}")
        print(f"失败: {self.failed}")
        print(f"耗时: {elapsed/60:.1f}分钟")


if __name__ == '__main__':
    updater = BatchUpdater()
    updater.run()
