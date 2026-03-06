#!/usr/bin/env python3
"""
收盘数据合并
交易时段结束后(15:00)自动将实时数据合并到历史K线
"""
import os, sys, time, json, requests, pandas as pd
from datetime import datetime, timedelta

for k in ['http_proxy', 'https_proxy']:
    os.environ.pop(k, None)

CACHE_DIR = os.path.expanduser('~/.openclaw/workspace/stock_cache/daily')
PORTFOLIO_FILE = os.path.expanduser('~/.openclaw/workspace/simulations/portfolio.json')

class EndOfDayMerger:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
    def is_market_close(self):
        """检查是否收盘"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        # 周一到周五
        if weekday >= 5:
            return False
        
        # 15:00 收盘
        if hour >= 15 and minute >= 0:
            return True
        return False
    
    def is_trading_hours(self):
        """检查是否在交易时间"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        if weekday >= 5:
            return False
        
        # 9:30-11:30
        if hour == 9 and minute >= 30:
            return True
        if 10 <= hour <= 11:
            return True
        
        # 13:00-15:00
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
    
    def get_realtime_data(self, symbol):
        """获取实时数据"""
        try:
            code = f'sh{symbol}' if symbol.startswith('6') or symbol.startswith('9') else f'sz{symbol}'
            r = self.session.get(f'https://qt.gtimg.cn/q={code}', timeout=5)
            if 'v_' in r.text:
                parts = r.text.split('=')[1].split('~')
                # 格式: 股票名,代码,现价,涨跌,涨跌%,买入,卖出,成交量,成交额...
                name = parts[0]
                price = float(parts[3]) if parts[3] else 0
                prev = float(parts[4]) if parts[4] else price
                high = float(parts[33]) if parts[33] else price
                low = float(parts[34]) if parts[34] else price
                vol = int(parts[36]) if parts[36] else 0
                amount = float(parts[37]) if parts[37] else 0
                open_price = float(parts[5]) if parts[5] else prev
                
                return {
                    '日期': datetime.now().strftime('%Y-%m-%d'),
                    '股票代码': symbol,
                    '开盘': open_price,
                    '收盘': price,
                    '最高': high,
                    '最低': low,
                    '成交量': vol,
                    '成交额': amount,
                    '振幅': round((high - low) / prev * 100, 2) if prev else 0,
                    '涨跌幅': round((price - prev) / prev * 100, 2) if prev else 0,
                    '涨跌额': round(price - prev, 2),
                    '换手率': 0  # 实时数据无换手率
                }
        except Exception as e:
            print(f"获取{symbol}失败: {e}")
        return None
    
    def merge_to_history(self, symbol, realtime_data):
        """合并到历史数据"""
        if not realtime_data:
            return False
            
        file_path = f'{CACHE_DIR}/{symbol}.csv'
        
        try:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                last_date = str(df.iloc[-1]['日期'])[:10]
                today = datetime.now().strftime('%Y-%m-%d')
                
                # 如果今天已有数据，更新最后一条
                if last_date == today:
                    df.iloc[-1] = realtime_data
                    print(f"  🔄 更新 {symbol}: {today}")
                else:
                    # 追加新数据
                    df = pd.concat([df, pd.DataFrame([realtime_data])], ignore_index=True)
                    print(f"  ➕ 新增 {symbol}: {today}")
            else:
                # 新建文件
                df = pd.DataFrame([realtime_data])
                print(f"  🆕 新建 {symbol}: {realtime_data['日期']}")
            
            df.to_csv(file_path, index=False)
            return True
            
        except Exception as e:
            print(f"  ❌ 合并失败 {symbol}: {e}")
            return False
    
    def run_realtime(self):
        """实时更新模式"""
        print("=" * 50)
        print("🖥️ 实时价格监控 + 收盘合并")
        print("⏰ 交易时间: 9:30-11:30, 13:00-15:00")
        print("📦 收盘后自动合并到历史数据")
        print("=" * 50)
        
        last_close_check = None
        
        while True:
            now = datetime.now()
            current_time = now.strftime('%H:%M')
            
            # 交易时段实时监控
            if self.is_trading_hours():
                portfolio = self.load_portfolio()
                positions = portfolio.get('positions', {})
                
                if positions:
                    print(f"\n🕐 {now.strftime('%H:%M:%S')} 交易时段")
                    
                    total_value = portfolio.get('cash', 0)
                    
                    for sym, pos in positions.items():
                        data = self.get_realtime_data(sym)
                        if data:
                            curr = data['收盘']
                            avg = pos.get('avg_price', curr)
                            shares = pos.get('shares', 0)
                            pnl = (curr - avg) * shares
                            pct = data['涨跌幅']
                            
                            emoji = "🟢" if pnl >= 0 else "🔴"
                            print(f"  {sym}: ¥{curr:.2f} ({pct:+.2f}%) {emoji}{pnl:+.0f}")
                            
                            total_value += curr * shares
                    
                    print(f"  💰 总资产: ¥{total_value:,.0f}")
                else:
                    print(f"\n🕐 {now.strftime('%H:%M:%S')} 无持仓")
            
            # 检查是否收盘 (15:00-15:05)
            if current_time >= "15:00" and current_time <= "15:05":
                if last_close_check != "15:00":
                    print("\n" + "=" * 50)
                    print("📦 收盘! 正在合并数据...")
                    print("=" * 50)
                    
                    portfolio = self.load_portfolio()
                    positions = portfolio.get('positions', {})
                    
                    for sym in positions.keys():
                        data = self.get_realtime_data(sym)
                        if data:
                            self.merge_to_history(sym, data)
                    
                    last_close_check = "15:00"
                    print("✅ 收盘数据合并完成!")
            
            # 非交易时段
            if not self.is_trading_hours() and not (current_time >= "15:00" and current_time <= "15:05"):
                print(f"\n🛌 {now.strftime('%H:%M')} 非交易时段，等待中...", end='\r')
            
            time.sleep(60)  # 每分钟更新


if __name__ == '__main__':
    EndOfDayMerger().run_realtime()
