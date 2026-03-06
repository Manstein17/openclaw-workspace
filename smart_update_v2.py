#!/usr/bin/env python3
"""
智能数据更新器
- 慢速获取，避免被封
- 自动检测API状态
- 失败后自动等待
"""
import os
import sys
import time
import random
import glob
import pandas as pd
import requests
from datetime import datetime

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')

class SmartUpdater:
    """智能更新器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        })
        
        # 配置
        self.BATCH_SIZE = 300  # 每批300只
        self.REQUEST_DELAY = 10  # 每次请求间隔3秒
        self.MAX_RETRIES = 3
        self.WAIT_TIME = 3600  # 被封后等待1小时
        
        self.updated = 0
        self.failed = 0
        self.blocked = False
    
    def get_stocks_to_update(self):
        """获取需要更新的股票"""
        stocks = []
        for f in glob.glob(f'{CACHE_DIR}/*.csv'):
            try:
                symbol = os.path.basename(f).replace('.csv', '')
                df = pd.read_csv(f)
                if len(df) > 0:
                    last_date = str(df.iloc[-1]['日期'])[:10]
                    if last_date not in ['2026-02-27', '2026-03-01']:
                        stocks.append(symbol)
                else:
                    stocks.append(symbol)
            except:
                stocks.append(symbol)
        
        random.shuffle(stocks)
        return stocks[:self.BATCH_SIZE]
    
    def get_sina_kline(self, symbol, days=30):
        """获取新浪K线数据"""
        url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
        params = {
            'symbol': f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}',
            'scale': '240',
            'ma': 'no',
            'datalen': days
        }
        
        for retry in range(self.MAX_RETRIES):
            try:
                time.sleep(self.REQUEST_DELAY + random.uniform(0, 1))
                r = self.session.get(url, params=params, timeout=10)
                
                if r.status_code == 200:
                    if '456' in r.text:
                        # 被限速
                        return {'error': 'blocked', 'retry': retry}
                    
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
                            return {'data': pd.DataFrame(records)}
                        
            except Exception as e:
                if retry == self.MAX_RETRIES - 1:
                    return {'error': str(e)}
        
        return {'error': 'max_retries'}
    
    def save_data(self, symbol, df):
        """保存数据"""
        path = f'{CACHE_DIR}/{symbol}.csv'
        df.to_csv(path, index=False)
    
    def run_batch(self):
        """运行一批更新"""
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 获取股票列表...")
        stocks = self.get_stocks_to_update()
        
        if not stocks:
            print("✅ 所有股票已是最新!")
            return True
        
        print(f"📊 需要更新: {len(stocks)}只")
        print(f"⏱️ 预计耗时: {len(stocks) * self.REQUEST_DELAY / 60:.0f}分钟")
        
        for i, symbol in enumerate(stocks):
            result = self.get_sina_kline(symbol)
            
            if result.get('error') == 'blocked':
                print(f"\n⚠️ 被限速! 等待 {self.WAIT_TIME/60:.0f}分钟后重试...")
                time.sleep(self.WAIT_TIME)
                # 重试这只
                result = self.get_sina_kline(symbol)
            
            if result.get('data') is not None:
                self.save_data(symbol, result['data'])
                self.updated += 1
            else:
                self.failed += 1
            
            if (i + 1) % 50 == 0:
                print(f"📊 进度: {i+1}/{len(stocks)} | 成功: {self.updated} | 失败: {self.failed}")
        
        return False
    
    def run(self):
        """主循环"""
        print("=== 智能数据更新器 ===")
        print(f"每批数量: {self.BATCH_SIZE}")
        print(f"请求间隔: {self.REQUEST_DELAY}秒")
        print(f"被封等待: {self.WAIT_TIME/60:.0f}分钟")
        print()
        
        round_num = 1
        while True:
            print(f"\n{'='*50}")
            print(f"第 {round_num} 轮更新")
            print(f"{'='*50}")
            
            done = self.run_batch()
            
            if done:
                print("\n✅ 全部完成!")
                break
            
            # 检查剩余
            remaining = len(self.get_stocks_to_update())
            if remaining == 0:
                print("\n✅ 全部完成!")
                break
            
            print(f"\n⏳ 1小时后继续... (剩余{remaining}只)")
            time.sleep(self.WAIT_TIME)
            round_num += 1


if __name__ == '__main__':
    updater = SmartUpdater()
    updater.run()
