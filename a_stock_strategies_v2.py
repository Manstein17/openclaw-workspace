"""
Lean策略集合 v2 - A股版 + 自动选择最佳策略
修复版 - 正确触发交易信号
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

INITIAL_CAPITAL = 100000
STOP_LOSS_PCT = 0.05

def get_stock_data(symbol, days=500):
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    df = ak.stock_zh_a_hist(symbol=symbol, period='daily', 
                            start_date=start_date, end_date=end_date, adjust='qfq')
    
    df = df.rename(columns={
        '日期': 'date', '开盘': 'open', '收盘': 'close',
        '最高': 'high', '最低': 'low', '成交量': 'volume'
    })
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def run_backtest(df, name, signal_col='position'):
    """通用回测"""
    capital = INITIAL_CAPITAL
    position = 0
    entry_price = 0
    trades = []
    
    for i, row in df.iterrows():
        if pd.isna(row.get(signal_col)) or pd.isna(row['close']):
            continue
        if i < 30:  # 预热期
            continue
        
        # 止损检查
        if position > 0:
            loss_pct = (row['close'] - entry_price) / entry_price
            if loss_pct <= -STOP_LOSS_PCT:
                revenue = position * row['close']
                capital += revenue
                trades.append({'action': 'STOP_LOSS', 'profit_pct': loss_pct * 100})
                print(f"  止损: {row['date'].strftime('%Y-%m-%d')} {loss_pct*100:.1f}%")
                position = 0
                entry_price = 0
                continue
        
        # 买入信号: position == 2 (从-1变到1，金叉)
        if row.get(signal_col) == 2 and position == 0 and capital > 0:
            shares = int((capital * 0.9) / row['close'])
            if shares > 0:
                capital -= shares * row['close']
                position = shares
                entry_price = row['close']
                print(f"  买入: {row['date'].strftime('%Y-%m-%d')} @{row['close']:.2f} x{shares}")
        
        # 卖出信号: position == -2 (从1变到-1，死叉)
        elif row.get(signal_col) == -2 and position > 0:
            revenue = position * row['close']
            capital += revenue
            profit_pct = (row['close'] - entry_price) / entry_price * 100
            trades.append({'action': 'SELL', 'profit_pct': profit_pct})
            print(f"  卖出: {row['date'].strftime('%Y-%m-%d')} @{row['close']:.2f} 盈利{profit_pct:.1f}%")
            position = 0
            entry_price = 0
    
    # 最终结算
    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = capital
    
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    sells = [t for t in trades if t['action'] == 'SELL']
    wins = len([t for t in sells if t['profit_pct'] > 0])
    
    return {
        'name': name,
        'return': total_return,
        'trades': len(sells),
        'wins': wins,
        'win_rate': wins / len(sells) * 100 if sells else 0
    }

# ============== 7大策略 ==============
def ma_crossover(df):
    """均线交叉"""
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['signal'] = np.where(df['ma5'] > df['ma20'], 1, -1)
    df['position'] = df['signal'].diff()
    return df

def rsi_strategy(df):
    """RSI策略"""
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # 金叉/死叉
    df['rsi_ma'] = df['rsi'].rolling(5).mean()
    df['signal'] = np.where(df['rsi'] > df['rsi_ma'], 1, -1)
    df['position'] = df['signal'].diff()
    return df

def macd_strategy(df):
    """MACD策略"""
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal_line']
    
    df['signal'] = np.where(df['histogram'] > 0, 1, -1)
    df['position'] = df['signal'].diff()
    return df

def bollinger_strategy(df):
    """布林带策略"""
    df['ma'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['upper'] = df['ma'] + 2 * df['std']
    df['lower'] = df['ma'] - 2 * df['std']
    
    # 价格触及下轨买入，上轨卖出
    df['signal'] = 0
    df.loc[df['close'] < df['lower'], 'signal'] = 1
    df.loc[df['close'] > df['upper'], 'signal'] = -1
    df['position'] = df['signal'].diff()
    return df

def momentum_strategy(df):
    """动量策略"""
    df['mom'] = df['close'].pct_change(10)
    df['signal'] = np.where(df['mom'] > 0, 1, -1)
    df['position'] = df['signal'].diff()
    return df

def ma_rsi_combo(df):
    """均线+RSI组合"""
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-10)))
    
    # MA
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    
    # 组合: 金叉且RSI<40 = 买入
    df['signal'] = 0
    df.loc[(df['ma5'] > df['ma20']) & (df['rsi'] < 40), 'signal'] = 1
    df.loc[(df['ma5'] < df['ma20']) & (df['rsi'] > 60), 'signal'] = -1
    df['position'] = df['signal'].diff()
    return df

def breakout_strategy(df):
    """20日高点突破"""
    df['highest'] = df['high'].rolling(20).max()
    df['lowest'] = df['low'].rolling(20).min()
    
    df['signal'] = 0
    df.loc[df['close'] > df['highest'].shift(1), 'signal'] = 1
    df.loc[df['close'] < df['lowest'].shift(1), 'signal'] = -1
    df['position'] = df['signal'].diff()
    return df

# ============== 主程序 ==============
def run_all(symbol='601318', name='中国平安'):
    print(f"\n{'='*50}")
    print(f"股票: {name} ({symbol})")
    print(f"{'='*50}")
    
    df = get_stock_data(symbol, days=500)
    print(f"数据: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
    
    strategies = [
        ('均线交叉', ma_crossover),
        ('RSI', rsi_strategy),
        ('MACD', macd_strategy),
        ('布林带', bollinger_strategy),
        ('动量', momentum_strategy),
        ('均线RSI组合', ma_rsi_combo),
        ('突破20日', breakout_strategy),
    ]
    
    results = []
    
    for sname, func in strategies:
        print(f"\n--- {sname} ---")
        df_copy = df.copy()
        df_copy = func(df_copy)
        result = run_backtest(df_copy, sname)
        results.append(result)
        print(f"  收益率: {result['return']:.2f}% | 交易: {result['trades']}次 | 胜率: {result['win_rate']:.0f}%")
    
    results.sort(key=lambda x: x['return'], reverse=True)
    
    print(f"\n{'='*50}")
    print("策略排名")
    print(f"{'='*50}")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['name']}: {r['return']:+.2f}% ({r['trades']}次)")
    
    return results

if __name__ == '__main__':
    stocks = [
        ('601318', '中国平安'),
        ('600036', '招商银行'),
        ('600519', '贵州茅台'),
    ]
    
    for symbol, name in stocks:
        results = run_all(symbol, name)
