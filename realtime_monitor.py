#!/usr/bin/env python3
"""
实时价格监控
交易时段(9:30-15:00)每分钟更新持仓价格
"""
import os, sys, time, json, requests
from datetime import datetime

for k in ['http_proxy', 'https_proxy']:
    os.environ.pop(k, None)

CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')
PORTFOLIO_FILE = os.path.expanduser('~/.openclaw/workspace/simulations/portfolio.json')

class RealtimeMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
    def is_trading_hours(self):
        """检查是否在交易时间"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        # 周一到周五
        if weekday >= 5:
            return False
        
        # 9:30-11:30 上午
        if hour == 9 and minute >= 30:
            return True
        if 10 <= hour <= 11:
            return True
        
        # 13:00-15:00 下午
        if 13 <= hour <= 14:
            return True
        if hour == 15 and minute == 0:
            return True
            
        return False
    
    def load_portfolio(self):
        """加载持仓"""
        try:
            with open(PORTFOLIO_FILE) as f:
                return json.load(f)
        except:
            return {'cash': 10000, 'positions': {}}
    
    def get_price(self, symbol):
        """获取实时价格"""
        try:
            code = f'sh{symbol}' if symbol.startswith('6') or symbol.startswith('9') else f'sz{symbol}'
            r = self.session.get(f'https://qt.gtimg.cn/q={code}', timeout=5)
            if 'v_' in r.text:
                parts = r.text.split('=')[1].split('~')
                price = float(parts[3]) if parts[3] else 0
                prev = float(parts[4]) if parts[4] else price
                pct = (price - prev) / prev * 100 if prev else 0
                return {'price': price, 'pct': pct, 'prev': prev}
        except Exception as e:
            print(f"获取{symbol}失败: {e}")
        return None
    
    def run(self):
        """主循环"""
        print("=" * 50)
        print("🖥️ 实时价格监控已启动")
        print("⏰ 交易时间: 9:30-11:30, 13:00-15:00")
        print("=" * 50)
        
        while True:
            if self.is_trading_hours():
                portfolio = self.load_portfolio()
                positions = portfolio.get('positions', {})
                
                if positions:
                    print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} 交易时段")
                    
                    total_value = portfolio.get('cash', 0)
                    
                    for sym, pos in positions.items():
                        data = self.get_price(sym)
                        if data:
                            curr = data['price']
                            avg = pos.get('avg_price', curr)
                            shares = pos.get('shares', 0)
                            pnl = (curr - avg) * shares
                            pct = data['pct']
                            
                            emoji = "🟢" if pnl >= 0 else "🔴"
                            print(f"  {sym}: ¥{curr:.2f} ({pct:+.2f}%) {emoji}{pnl:+.0f}")
                            
                            total_value += curr * shares
                    
                    print(f"  💰 总资产: ¥{total_value:,.0f}")
                else:
                    print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} 无持仓")
            else:
                now = datetime.now()
                print(f"\n🛌 {now.strftime('%H:%M')} 非交易时段，等待中...", end='\r')
            
            time.sleep(60)  # 每分钟更新


if __name__ == '__main__':
    RealtimeMonitor().run()
