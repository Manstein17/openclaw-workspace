#!/usr/bin/env python3
"""
谨慎数据更新脚本
- 慢速获取，避免封禁
- 每天最多更新500只
- 每次请求间隔2秒
- 失败重试3次
"""
import os
import sys
import time
import random
import glob
import pandas as pd
import requests

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

# 配置
CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')
MAX_UPDATES_PER_DAY = 500  # 每天最多更新500只
REQUEST_DELAY = 2  # 每次请求间隔2秒
MAX_RETRIES = 3

class CarefulUpdater:
    """谨慎的数据更新器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        self.updated = 0
        self.failed = 0
    
    def get_stock_list(self):
        """获取需要更新的股票列表"""
        stocks = []
        
        for f in glob.glob(f'{CACHE_DIR}/*.csv'):
            try:
                symbol = os.path.basename(f).replace('.csv', '')
                
                # 读取当前数据
                df = pd.read_csv(f)
                if len(df) > 0:
                    last_date = str(df.iloc[-1]['日期'])[:10]
                    
                    # 需要更新的条件
                    if last_date != '2026-02-27' and last_date != '2026-03-01':
                        stocks.append(symbol)
                else:
                    stocks.append(symbol)
            except:
                stocks.append(symbol)
        
        # 随机打乱顺序
        random.shuffle(stocks)
        
        # 限制数量
        return stocks[:MAX_UPDATES_PER_DAY]
    
    def get_sina_kline(self, symbol, days=30):
        """获取新浪K线数据"""
        url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
        params = {
            'symbol': f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}',
            'scale': '240',  # 日线
            'ma': 'no',
            'datalen': days
        }
        
        for retry in range(MAX_RETRIES):
            try:
                r = self.session.get(url, params=params, timeout=10)
                
                if r.status_code == 200:
                    data = r.json()
                    
                    if data and isinstance(data, list):
                        # 转换为DataFrame
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
                
                # 456表示被限速
                if '456' in r.text:
                    print(f"   ⚠️ 限速，等待60秒...")
                    time.sleep(60)
                    continue
                    
            except Exception as e:
                print(f"   错误: {e}")
                time.sleep(5)
        
        return None
    
    def save_data(self, symbol, df):
        """保存数据"""
        path = f'{CACHE_DIR}/{symbol}.csv'
        df.to_csv(path, index=False)
    
    def update_stock(self, symbol):
        """更新单只股票"""
        print(f"📥 {symbol}...", end=' ')
        
        df = self.get_sina_kline(symbol)
        
        if df is not None and len(df) > 0:
            self.save_data(symbol, df)
            print(f"✅ {len(df)}条")
            self.updated += 1
        else:
            print(f"❌ 失败")
            self.failed += 1
    
    def run(self):
        """运行更新"""
        print("=== 谨慎数据更新 ===")
        print(f"每天最多更新: {MAX_UPDATES_PER_DAY}只")
        print(f"请求间隔: {REQUEST_DELAY}秒")
        print()
        
        stocks = self.get_stock_list()
        print(f"需要更新: {len(stocks)}只\n")
        
        for i, symbol in enumerate(stocks):
            self.update_stock(symbol)
            
            # 随机延迟，避免固定频率
            delay = REQUEST_DELAY + random.uniform(0, 1)
            time.sleep(delay)
            
            # 每50个报告一次
            if (i + 1) % 50 == 0:
                print(f"\n📊 进度: {i+1}/{len(stocks)} | 成功: {self.updated} | 失败: {self.failed}")
                print()
        
        print(f"\n=== 完成 ===")
        print(f"成功: {self.updated}")
        print(f"失败: {self.failed}")


if __name__ == '__main__':
    updater = CarefulUpdater()
    updater.run()
