"""
A股全自动交易系统 - 模拟实盘版
目标: 每天扫描市场 + 自动选择最佳策略 + 模拟交易
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# ============== 配置 ==============
INITIAL_CAPITAL = 10000  # 初始1万
MAX_POSITIONS = 3         # 最多持仓3只
STOP_LOSS_PCT = 0.05     # 5%止损
TAKE_PROFIT_PCT = 0.10   # 10%止盈

# 股票池 - 分散投资
STOCK_POOL = [
    # 蓝筹股
    ('601318', '中国平安'),
    ('600036', '招商银行'),
    ('600519', '贵州茅台'),
    ('000858', '五粮液'),
    ('600030', '中信证券'),
    ('601888', '中国中免'),
    ('600900', '长江电力'),
    # ETF
    ('510300', '沪深300ETF'),
    ('510500', '500ETF'),
    ('159919', '券商ETF'),
    ('159995', '券商ETF'),
    # 成长股
    ('300750', '宁德时代'),
    ('002594', '比亚迪'),
    ('600276', '恒瑞医药'),
    ('000333', '美的集团'),
]

# ============== 数据获取 ==============
def get_recent_data(symbol, days=60):
    """获取近期数据用于选股"""
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')
    
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                 start_date=start_date, end_date=end_date, adjust='qfq')
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        })
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df.tail(days)  # 只返回最近days天
    except:
        return None

# ============== 策略库 ==============
def ma_crossover(df):
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['signal'] = np.where(df['ma5'] > df['ma10'], 1, -1)
    df['position'] = df['signal'].diff()
    return df

def rsi_strategy(df):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi_ma'] = df['rsi'].rolling(5).mean()
    df['signal'] = np.where(df['rsi'] > df['rsi_ma'], 1, -1)
    df['position'] = df['signal'].diff()
    return df

def macd_strategy(df):
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal_line']
    df['signal'] = np.where(df['histogram'] > 0, 1, -1)
    df['position'] = df['signal'].diff()
    return df

def momentum_strategy(df):
    df['mom'] = df['close'].pct_change(5)
    df['signal'] = np.where(df['mom'] > 0, 1, -1)
    df['position'] = df['signal'].diff()
    return df

STRATEGIES = {
    '均线交叉': ma_crossover,
    'RSI': rsi_strategy,
    'MACD': macd_strategy,
    '动量': momentum_strategy,
}

# ============== 快速回测 ==============
def quick_backtest(df, strategy_func, days=30):
    """快速回测最近N天"""
    if len(df) < days + 10:
        return None
    
    df = strategy_func(df.copy())
    test_df = df.tail(days).copy()
    
    capital = INITIAL_CAPITAL * 0.3  # 用30%仓位测试
    position = 0
    entry_price = 0
    wins = 0
    trades = 0
    
    for i, row in test_df.iterrows():
        if pd.isna(row.get('position')):
            continue
        
        # 买入信号
        if row['position'] == 2 and position == 0 and capital > 0:
            shares = int((capital * 0.9) / row['close'])
            if shares > 0:
                capital -= shares * row['close']
                position = shares
                entry_price = row['close']
        
        # 卖出信号
        elif row['position'] == -2 and position > 0:
            revenue = position * row['close']
            profit_pct = (row['close'] - entry_price) / entry_price
            if profit_pct > 0:
                wins += 1
            trades += 1
            capital += revenue
            position = 0
    
    if position > 0:
        final_value = capital + position * test_df.iloc[-1]['close']
    else:
        final_value = capital
    
    total_return = (final_value - INITIAL_CAPITAL * 0.3) / (INITIAL_CAPITAL * 0.3)
    
    return {
        'return': total_return * 100,
        'trades': trades,
        'wins': wins,
        'win_rate': wins / trades * 100 if trades > 0 else 0
    }

# ============== 市场扫描 ==============
def scan_market():
    """扫描市场，找到最佳股票+策略组合"""
    print("="*60)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 市场扫描")
    print("="*60)
    
    opportunities = []
    
    for symbol, name in STOCK_POOL:
        print(f"扫描: {name}...", end=" ")
        df = get_recent_data(symbol, days=60)
        
        if df is None or len(df) < 40:
            print("数据不足")
            continue
        
        # 测试每个策略
        best_strategy = None
        best_return = -999
        
        for sname, sfunc in STRATEGIES.items():
            result = quick_backtest(df, sfunc, days=20)
            if result and result['return'] > best_return:
                best_return = result['return']
                best_strategy = {
                    'name': sname,
                    'return': result['return'],
                    'trades': result['trades'],
                    'win_rate': result['win_rate']
                }
        
        if best_strategy and best_return > -10:  # 亏损小于10%的才考虑
            opportunities.append({
                'symbol': symbol,
                'name': name,
                'strategy': best_strategy['name'],
                'return': best_return,
                'win_rate': best_strategy['win_rate'],
                'trades': best_strategy['trades'],
                'price': df.iloc[-1]['close']
            })
            print(f"✓ {best_strategy['name']} {best_return:+.1f}%")
        else:
            print("✗")
    
    # 按收益率排序
    opportunities.sort(key=lambda x: x['return'], reverse=True)
    
    return opportunities

# ============== 交易模拟 ==============
class PaperTrader:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.positions = {}  # {symbol: {'shares': x, 'entry': y}}
        self.history = []
    
    def buy(self, symbol, name, price, strategy):
        """买入"""
        if len(self.positions) >= MAX_POSITIONS:
            return False
        
        if self.cash < price * 100:
            return False
        
        shares = int((self.cash * 0.3) / price)  # 用30%资金
        cost = shares * price
        
        self.positions[symbol] = {
            'name': name,
            'shares': shares,
            'entry': price,
            'strategy': strategy,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        self.cash -= cost
        
        print(f"\n📈 买入 {name} ({symbol})")
        print(f"   价格: {price:.2f}, 股数: {shares}, 金额: {cost:.2f}")
        print(f"   策略: {strategy}")
        
        return True
    
    def sell(self, symbol, reason=''):
        """卖出"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        current_price = None
        
        # 获取当前价格
        for s, n in STOCK_POOL:
            if s == symbol:
                df = get_recent_data(s, days=5)
                if df is not None:
                    current_price = df.iloc[-1]['close']
                break
        
        if current_price is None:
            return
        
        revenue = pos['shares'] * current_price
        profit_pct = (current_price - pos['entry']) / pos['entry'] * 100
        
        self.cash += revenue
        
        print(f"\n📉 卖出 {pos['name']} ({symbol}) - {reason}")
        print(f"   价格: {current_price:.2f}, 盈利: {profit_pct:+.2f}%")
        
        self.history.append({
            'symbol': symbol,
            'name': pos['name'],
            'entry': pos['entry'],
            'exit': current_price,
            'profit_pct': profit_pct,
            'strategy': pos['strategy'],
            'date': pos['date'],
            'exit_date': datetime.now().strftime('%Y-%m-%d')
        })
        
        del self.positions[symbol]
    
    def check_positions(self):
        """检查持仓是否需要止损/止盈"""
        for symbol in list(self.positions.keys()):
            pos = self.positions[symbol]
            
            # 获取当前价格
            df = get_recent_data(symbol, days=5)
            if df is None or len(df) == 0:
                continue
            
            current_price = df.iloc[-1]['close']
            profit_pct = (current_price - pos['entry']) / pos['entry']
            
            # 止损
            if profit_pct <= -STOP_LOSS_PCT:
                self.sell(symbol, '止损')
            # 止盈
            elif profit_pct >= TAKE_PROFIT_PCT:
                self.sell(symbol, '止盈')
    
    def generate_signals(self):
        """生成今日信号"""
        signals = scan_market()
        
        # 过滤掉已持仓的
        available = [s for s in signals if s['symbol'] not in self.positions]
        
        # 取前3
        top_signals = available[:3]
        
        return top_signals
    
    def status(self):
        """当前状态"""
        total_value = self.cash
        
        print("\n" + "="*50)
        print("📊 当前持仓状态")
        print("="*50)
        
        for symbol, pos in self.positions.items():
            df = get_recent_data(symbol, days=5)
            if df is not None and len(df) > 0:
                current = df.iloc[-1]['close']
                profit_pct = (current - pos['entry']) / pos['entry'] * 100
                value = pos['shares'] * current
                total_value += value
                
                print(f"  {pos['name']} ({symbol})")
                print(f"    买入: {pos['entry']:.2f}, 当前: {current:.2f}")
                print(f"    盈亏: {profit_pct:+.2f}%")
                print(f"    策略: {pos['strategy']}")
        
        print(f"\n现金: {self.cash:.2f}")
        print(f"总资产: {total_value:.2f}")
        print(f"收益率: {(total_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100:+.2f}%")
        
        return total_value

# ============== 主程序 ==============
def run_daily():
    """每日运行"""
    trader = PaperTrader()
    
    # 检查持仓
    print("\n🔍 检查持仓...")
    trader.check_positions()
    
    # 生成信号
    print("\n🎯 今日信号:")
    signals = trader.generate_signals()
    
    if signals:
        print("\n推荐交易:")
        for i, sig in enumerate(signals, 1):
            print(f"  {i}. {sig['name']} ({sig['symbol']})")
            print(f"     策略: {sig['strategy']}, 预期收益: {sig['return']:+.1f}%")
            print(f"     现价: {sig['price']:.2f}, 胜率: {sig['win_rate']:.0f}%")
            
            # 自动买入
            trader.buy(sig['symbol'], sig['name'], sig['price'], sig['strategy'])
    
    # 显示状态
    trader.status()
    
    return trader

# ============== 加载/保存状态 ==============
def save_state(trader, filename='trader_state.json'):
    state = {
        'cash': trader.cash,
        'positions': trader.positions,
        'history': trader.history,
        'last_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    with open(filename, 'w') as f:
        json.dump(state, f, indent=2)

def load_state(filename='trader_state.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            state = json.load(f)
            return state
    return None

if __name__ == '__main__':
    run_daily()
