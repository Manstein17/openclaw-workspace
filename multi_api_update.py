#!/usr/bin/env python3
"""
多API源数据更新器
新浪+腾讯+东财 轮流使用，避免限速
"""
import os, sys, time, random, glob, pandas as pd, requests
from datetime import datetime

for k in ['http_proxy', 'https_proxy']:
    os.environ.pop(k, None)

CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')

class MultiAPIUpdater:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.updated = 0
        self.failed = 0
        self.wait_time = 120  # 被限速后等待60秒
        
    def get_stocks(self):
        stocks = []
        for f in glob.glob(f'{CACHE_DIR}/*.csv'):
            symbol = os.path.basename(f).replace('.csv', '')
            try:
                df = pd.read_csv(f)
                if len(df) > 0:
                    d = str(df.iloc[-1]['日期'])[:10]
                    if d not in ['2026-03-02', '2026-03-03']:
                        stocks.append(symbol)
                else:
                    stocks.append(symbol)
            except:
                stocks.append(symbol)
        random.shuffle(stocks)
        return stocks[:200]  # 每次只更新200只
    
    def get_sina(self, symbol):
        """新浪API"""
        try:
            url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
            params = {'symbol': f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}', 
                     'scale': '240', 'ma': 'no', 'datalen': '30'}
            r = self.session.get(url, params=params, timeout=10)
            if '456' in r.text:
                return None, 'sina_blocked'
            data = r.json()
            if data and isinstance(data, list):
                records = [{'日期': i['day'], '股票代码': symbol, '开盘': float(i['open']),
                          '收盘': float(i['close']), '最高': float(i['high']), 
                          '最低': float(i['low']), '成交量': int(i['volume'])} for i in data]
                return pd.DataFrame(records), 'sina'
        except Exception as e:
            return None, str(e)
        return None, 'fail'
    
    def get_tencent(self, symbol):
        """腾讯API"""
        try:
            code = f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}'
            url = f'https://web.ifzq.gtimg.cn/appstock/app/fqchart_google/data?symbol={code}&period=day&type=qfq&end=20260303'
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get('data'):
                    chart = data['data'].get(code, {})
                    klines = chart.get('data', [])
                    if klines:
                        records = []
                        for k in klines:
                            if len(k) >= 6:
                                records.append({'日期': k[0], '股票代码': symbol, '开盘': float(k[1]),
                                             '收盘': float(k[2]), '最高': float(k[3]), '最低': float(k[4]), '成交量': int(k[5])})
                        return pd.DataFrame(records), 'tencent'
        except Exception as e:
            return None, str(e)
        return None, 'fail'
    
    def save(self, symbol, df):
        if df is not None and len(df) > 0:
            df.to_csv(f'{CACHE_DIR}/{symbol}.csv', index=False)
            return True
        return False
    
    def update_one(self, symbol):
        # 尝试新浪
        df, status = self.get_sina(symbol)
        if df is not None:
            if self.save(symbol, df):
                self.updated += 1
                return True, 'sina'
        
        time.sleep(5)  # 等待
        
        # 尝试腾讯
        df, status = self.get_tencent(symbol)
        if df is not None:
            if self.save(symbol, df):
                self.updated += 1
                return True, 'tencent'
        
        self.failed += 1
        return False, status
    
    def run(self):
        stocks = self.get_stocks()
        print(f"需要更新: {len(stocks)}只")
        
        for i, sym in enumerate(stocks):
            ok, status = self.update_one(sym)
            
            if status == 'sina_blocked':
                print(f"⚠️ 被限速，等待{self.wait_time}秒...")
                time.sleep(self.wait_time)
            
            if (i + 1) % 20 == 0:
                print(f"进度: {i+1}/{len(stocks)} | 成功: {self.updated} | 失败: {self.failed}")
        
        print(f"完成! 成功: {self.updated}, 失败: {self.failed}")


if __name__ == '__main__':
    MultiAPIUpdater().run()
