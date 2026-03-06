#!/usr/bin/env python3
"""
数据健康监测 + 自动更新
定时检查股票数据是否为最新，不是最新则自动更新
"""
import os, sys, time, json, glob, pandas as pd, requests, random
from datetime import datetime, timedelta

for k in ['http_proxy', 'https_proxy']:
    os.environ.pop(k, None)

CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')
PORTFOLIO_FILE = os.path.expanduser('~/.openclaw/workspace/simulations/portfolio.json')

class DataHealthMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        self.updated_today = 0
        self.REQUEST_DELAY = 10  # 请求间隔10秒
        
    def get_latest_date(self, symbol):
        """获取股票最新数据日期"""
        file_path = f'{CACHE_DIR}/{symbol}.csv'
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                if len(df) > 0:
                    return str(df.iloc[-1]['日期'])[:10]
        except:
            pass
        return None
    
    def is_data_fresh(self, symbol):
        """检查数据是否为最新"""
        latest = self.get_latest_date(symbol)
        if not latest:
            return False
        
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 今天是周六/周日，检查周五
        weekday = datetime.now().weekday()
        if weekday >= 5:  # 周六日
            friday = (datetime.now() - timedelta(days=weekday - 4)).strftime('%Y-%m-%d')
            return latest == friday
        
        # 工作日，检查今天或昨天
        return latest in [today, yesterday]
    
    def get_stale_stocks(self, limit=50):
        """获取需要更新的股票"""
        stale = []
        
        # 优先检查持仓股票
        portfolio = self.load_portfolio()
        positions = portfolio.get('positions', {})
        for sym in positions.keys():
            if not self.is_data_fresh(sym):
                stale.append(sym)
        
        # 然后随机检查其他股票
        files = glob.glob(f'{CACHE_DIR}/*.csv')
        random.shuffle(files)
        
        for f in files[:200]:  # 随机检查200只
            symbol = os.path.basename(f).replace('.csv', '')
            if symbol not in positions and not self.is_data_fresh(symbol):
                stale.append(symbol)
                if len(stale) >= limit:
                    break
        
        return stale
    
    def load_portfolio(self):
        """加载持仓"""
        try:
            with open(PORTFOLIO_FILE) as f:
                return json.load(f)
        except:
            return {'cash': 10000, 'positions': {}}
    
    def get_sina_kline(self, symbol):
        """获取新浪K线"""
        try:
            url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
            params = {
                'symbol': f'sh{symbol}' if symbol.startswith('6') or symbol.startswith('9') else f'sz{symbol}',
                'scale': '240',
                'ma': 'no',
                'datalen': '30'
            }
            r = self.session.get(url, params=params, timeout=10)
            
            if '456' in r.text:
                return None, 'blocked'
            
            data = r.json()
            if data and isinstance(data, list):
                records = []
                for i in data:
                    try:
                        records.append({
                            '日期': i['day'],
                            '股票代码': symbol,
                            '开盘': float(i['open']),
                            '收盘': float(i['close']),
                            '最高': float(i['high']),
                            '最低': float(i['low']),
                            '成交量': int(i['volume'])
                        })
                    except:
                        pass
                return pd.DataFrame(records), 'ok'
        except Exception as e:
            return None, str(e)
        return None, 'fail'
    
    def update_stock(self, symbol):
        """更新单只股票"""
        df, status = self.get_sina_kline(symbol)
        
        if df is not None and len(df) > 0:
            file_path = f'{CACHE_DIR}/{symbol}.csv'
            df.to_csv(file_path, index=False)
            self.updated_today += 1
            return True, status
        
        return False, status
    
    def run(self):
        """主循环"""
        print("=" * 50)
        print("🔍 数据健康监测 + 自动更新")
        print("⏰ 检查周期: 每30分钟")
        print("=" * 50)
        
        last_check = None
        
        while True:
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            
            # 每30分钟检查一次
            minute = now.minute
            if minute % 30 == 0 and last_check != current_time:
                print(f"\n🔍 {now.strftime('%Y-%m-%d %H:%M')} 开始检查数据健康...")
                
                stale = self.get_stale_stocks(limit=50)
                
                if stale:
                    print(f"发现 {len(stale)} 只股票数据不是最新:")
                    
                    # 优先更新持仓
                    portfolio = self.load_portfolio()
                    positions = portfolio.get('positions', {})
                    
                    priority = [s for s in stale if s in positions]
                    others = [s for s in stale if s not in positions]
                    
                    to_update = priority + others[:20]  # 优先更新持仓 + 最多20只
                    
                    for i, sym in enumerate(to_update):
                        print(f"  更新 {sym}...", end=" ")
                        ok, status = self.update_stock(sym)
                        if ok:
                            print("✅")
                        else:
                            print(f"⚠️ {status}")
                        
                        if status == 'blocked':
                            print(f"  被限速，等待60秒...")
                            time.sleep(60)
                        else:
                            time.sleep(self.REQUEST_DELAY + random.uniform(0, 2))
                        
                        if (i + 1) % 10 == 0:
                            print(f"  已更新 {i+1}/{len(to_update)}")
                    
                    print(f"✅ 数据更新完成! 本次更新: {len(to_update)}只")
                else:
                    print("✅ 所有数据都是最新的!")
                
                last_check = current_time
            else:
                print(f"\n🛌 {now.strftime('%H:%M')} 等待下次检查...", end='\r')
            
            time.sleep(60)


if __name__ == '__main__':
    DataHealthMonitor().run()
