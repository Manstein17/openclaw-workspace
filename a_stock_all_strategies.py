"""
Lean策略集合 - A股版 + 自动选择最佳策略
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# ============== 基础设置 ==============
INITIAL_CAPITAL = 100000
STOP_LOSS_PCT = 0.05

# ============== 数据获取 ==============
def get_stock_data(symbol, days=500):
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period='daily',
        start_date=start_date,
        end_date=end_date,
        adjust='qfq'
    )
    
    df = df.rename(columns={
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume'
    })
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

# ============== 基础策略类 ==============
class BaseStrategy(ABC):
    name = "Base"
    
    @abstractmethod
    def generate_signals(self, df):
        """生成交易信号"""
        pass
    
    def backtest(self, df, initial_capital=INITIAL_CAPITAL):
        capital = initial_capital
        position = 0
        entry_price = 0
        trades = []
        
        df = self.generate_signals(df)
        
        for i, row in df.iterrows():
            if pd.isna(row.get('position')) or pd.isna(row['close']):
                continue
            
            # 止损
            if position > 0:
                loss_pct = (row['close'] - entry_price) / entry_price
                if loss_pct <= -STOP_LOSS_PCT:
                    revenue = position * row['close']
                    capital += revenue
                    trades.append({'action': 'STOP_LOSS', 'profit_pct': loss_pct * 100})
                    position = 0
                    entry_price = 0
                    continue
            
            if position > 0:
                continue
            
            # 买入
            if row.get('position') == 2 and capital > 0:
                shares = int((capital * 0.9) / row['close'])
                if shares > 0:
                    capital -= shares * row['close']
                    position = shares
                    entry_price = row['close']
            
            # 卖出
            elif row.get('position') == -2 and position > 0:
                revenue = position * row['close']
                capital += revenue
                profit_pct = (row['close'] - entry_price) / entry_price * 100
                trades.append({'action': 'SELL', 'profit_pct': profit_pct})
                position = 0
                entry_price = 0
        
        final_value = capital + (position * df.iloc[-1]['close'] if position > 0 else 0)
        total_return = (final_value - initial_capital) / initial_capital * 100
        
        wins = len([t for t in trades if t.get('profit_pct', 0) > 0])
        total_trades = len([t for t in trades if t['action'] == 'SELL'])
        
        return {
            'name': self.name,
            'total_return': total_return,
            'total_trades': total_trades,
            'wins': wins,
            'win_rate': (wins / total_trades * 100) if total_trades > 0 else 0,
            'final_value': final_value
        }

# ============== 策略1: 均线交叉 ==============
class MAIntersection(BaseStrategy):
    name = "均线交叉"
    
    def generate_signals(self, df):
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['signal'] = 0
        df.loc[df['ma5'] > df['ma20'], 'signal'] = 1
        df.loc[df['ma5'] <= df['ma20'], 'signal'] = -1
        df['position'] = df['signal'].diff()
        return df

# ============== 策略2: RSI超买超卖 ==============
class RSIStrategy(BaseStrategy):
    name = "RSI"
    
    def generate_signals(self, df, period=14, oversold=30, overbought=70):
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['signal'] = 0
        df.loc[df['rsi'] < oversold, 'signal'] = 1   # 超卖买入
        df.loc[df['rsi'] > overbought, 'signal'] = -1 # 超卖卖出
        df['position'] = df['signal'].diff()
        
        # 只在金叉/死叉时交易
        df.loc[df['position'] != 2, 'position'] = 0
        return df

# ============== 策略3: MACD ==============
class MACDStrategy(BaseStrategy):
    name = "MACD"
    
    def generate_signals(self, df, fast=12, slow=26, signal=9):
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal_line'] = df['macd'].ewm(span=signal, adjust=False).mean()
        df['histogram'] = df['macd'] - df['signal_line']
        
        df['signal'] = 0
        df.loc[df['histogram'] > 0, 'signal'] = 1
        df.loc[df['histogram'] <= 0, 'signal'] = -1
        df['position'] = df['signal'].diff()
        
        return df

# ============== 策略4: 布林带 ==============
class BollingerStrategy(BaseStrategy):
    name = "布林带"
    
    def generate_signals(self, df, window=20, num_std=2):
        df['ma'] = df['close'].rolling(window).mean()
        df['std'] = df['close'].rolling(window).std()
        df['upper'] = df['ma'] + num_std * df['std']
        df['lower'] = df['ma'] - num_std * df['std']
        
        df['signal'] = 0
        df.loc[df['close'] < df['lower'], 'signal'] = 1  # 触及下轨买入
        df.loc[df['close'] > df['upper'], 'signal'] = -1 # 触及上轨卖出
        df['position'] = df['signal'].diff()
        
        return df

# ============== 策略5: 动量策略 ==============
class MomentumStrategy(BaseStrategy):
    name = "动量"
    
    def generate_signals(self, df, period=10):
        df['momentum'] = df['close'].pct_change(period)
        
        df['signal'] = 0
        df.loc[df['momentum'] > 0.02, 'signal'] = 1   # 上涨超过2%买入
        df.loc[df['momentum'] < -0.02, 'signal'] = -1 # 下跌超过2%卖出
        df['position'] = df['signal'].diff()
        
        return df

# ============== 策略6: 双均线+RSI组合 ==============
class MARSICombo(BaseStrategy):
    name = "均线RSI组合"
    
    def generate_signals(self, df):
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / loss))
        
        # MA
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        
        # 组合信号
        df['signal'] = 0
        # 金叉 + RSI超卖 = 买入
        df.loc[(df['ma5'] > df['ma20']) & (df['rsi'] < 35), 'signal'] = 1
        # 死叉 + RSI超买 = 卖出
        df.loc[(df['ma5'] <= df['ma20']) & (df['rsi'] > 65), 'signal'] = -1
        
        df['position'] = df['signal'].diff()
        return df

# ============== 策略7: 突破策略 ==============
class BreakoutStrategy(BaseStrategy):
    name = "突破20日最高"
    
    def generate_signals(self, df, period=20):
        df['highest'] = df['high'].rolling(period).max()
        
        df['signal'] = 0
        df.loc[df['close'] > df['highest'].shift(1), 'signal'] = 1
        df.loc[df['close'] < df['low'].rolling(period).min().shift(1), 'signal'] = -1
        df['position'] = df['signal'].diff()
        
        return df

# ============== 主程序 ==============
def run_all_strategies(symbol='601318'):
    print("="*60)
    print(f"股票: {symbol} - 全策略回测")
    print("="*60)
    
    df = get_stock_data(symbol, days=500)
    print(f"数据范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
    
    strategies = [
        MAIntersection(),
        RSIStrategy(),
        MACDStrategy(),
        BollingerStrategy(),
        MomentumStrategy(),
        MARSICombo(),
        BreakoutStrategy(),
    ]
    
    results = []
    
    for strategy in strategies:
        try:
            result = strategy.backtest(df.copy())
            results.append(result)
            print(f"\n{strategy.name}:")
            print(f"  收益率: {result['total_return']:.2f}%")
            print(f"  交易次数: {result['total_trades']}")
            print(f"  胜率: {result['win_rate']:.1f}%")
        except Exception as e:
            print(f"\n{strategy.name}: 错误 - {e}")
    
    # 排序选择最佳策略
    if results:
        results.sort(key=lambda x: x['total_return'], reverse=True)
        
        print("\n" + "="*60)
        print("策略排名（按收益率）")
        print("="*60)
        for i, r in enumerate(results, 1):
            print(f"{i}. {r['name']}: {r['total_return']:.2f}% (交易{r['total_trades']}次, 胜率{r['win_rate']:.1f}%)")
        
        best = results[0]
        print(f"\n🏆 最佳策略: {best['name']}")
        print(f"   收益率: {best['total_return']:.2f}%")
        
        return results

if __name__ == '__main__':
    stocks = [
        ('601318', '中国平安'),
        ('600036', '招商银行'),
        ('000001', '平安银行'),
        ('600030', '中信证券'),
    ]
    
    all_results = {}
    
    for symbol, name in stocks:
        print("\n" + "█"*60)
        results = run_all_strategies(symbol)
        all_results[name] = results
