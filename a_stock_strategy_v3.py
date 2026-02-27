"""
A股均线交叉策略 v3 - 带趋势/震荡过滤
移植自Lean + 市场状态判断
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============== 策略参数 ==============
SHORT_WINDOW = 5
LONG_WINDOW = 20
ATR_WINDOW = 14      # ATR周期
ATR_MULT = 2.0       # ATR倍数（判断震荡）
STOP_LOSS_PCT = 0.05
INITIAL_CAPITAL = 100000

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

# ============== 趋势/震荡判断 ==============
def calculate_atr(df, period=14):
    """计算ATR（平均真实波幅）"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(period).mean()
    return atr

def calculate_trend_strength(df):
    """
    判断趋势强度
    使用ATR与收盘价的比率 + 均线斜率
    返回: 1=趋势, 0=震荡
    """
    # ATR占收盘价的比率
    df['atr'] = calculate_atr(df, ATR_WINDOW)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    
    # 均线斜率
    df['ma20'] = df['close'].rolling(20).mean()
    df['ma_slope'] = (df['ma20'] - df['ma20'].shift(10)) / df['ma20'].shift(10) * 100
    
    # 趋势判断条件
    # 1. ATR波动足够大 (>2%收盘价)
    # 2. 均线有斜率 (不是横着走)
    df['is_trend'] = 0
    df.loc[(df['atr_pct'] > 2.0) & (np.abs(df['ma_slope']) > 2), 'is_trend'] = 1
    
    # 震荡标记
    df['market_regime'] = '震荡'
    df.loc[df['is_trend'] == 1, 'market_regime'] = '趋势'
    
    return df

def generate_signals(df):
    """生成交易信号"""
    df['short_ma'] = df['close'].rolling(SHORT_WINDOW).mean()
    df['long_ma'] = df['close'].rolling(LONG_WINDOW).mean()
    
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] <= df['long_ma'], 'signal'] = -1
    df['position'] = df['signal'].diff()
    
    return df

# ============== 回测引擎 ==============
def backtest(df, name):
    capital = INITIAL_CAPITAL
    position = 0
    entry_price = 0
    trades = []
    skipped = 0
    
    for i, row in df.iterrows():
        if pd.isna(row.get('position')) or pd.isna(row['close']):
            continue
        
        # 检查市场状态 - 震荡时不交易
        is_trend = row.get('is_trend', 0)
        
        # 止损检查
        if position > 0:
            loss_pct = (row['close'] - entry_price) / entry_price
            if loss_pct <= -STOP_LOSS_PCT:
                revenue = position * row['close']
                capital += revenue
                trades.append({
                    'date': row['date'], 'action': 'STOP_LOSS',
                    'price': row['close'], 'shares': position,
                    'revenue': revenue, 'regime': row.get('market_regime', '未知')
                })
                print(f"止损 {row['date'].strftime('%Y-%m-%d')}: "
                      f"{row.get('market_regime', 'N/A')} | 价格={row['close']:.2f}")
                position = 0
                entry_price = 0
                continue
        
        if position > 0:
            continue
        
        # 只在趋势市场交易
        if is_trend == 1:
            if row.get('position') == 2 and capital > 0:
                buy_amount = capital * 0.9
                shares = int(buy_amount / row['close'])
                if shares > 0:
                    cost = shares * row['close']
                    capital -= cost
                    position = shares
                    entry_price = row['close']
                    trades.append({
                        'date': row['date'], 'action': 'BUY',
                        'price': row['close'], 'shares': shares,
                        'regime': row.get('market_regime', '趋势')
                    })
                    print(f"买入 {row['date'].strftime('%Y-%m-%d')}: "
                          f"趋势 | 价格={row['close']:.2f}, 股数={shares}")
        else:
            skipped += 1
            
        # 卖出
        if row.get('position') == -2 and position > 0:
            revenue = position * row['close']
            capital += revenue
            profit_pct = (row['close'] - entry_price) / entry_price * 100
            trades.append({
                'date': row['date'], 'action': 'SELL',
                'price': row['close'], 'shares': position,
                'revenue': revenue, 'profit_pct': profit_pct,
                'regime': row.get('market_regime', '趋势')
            })
            print(f"卖出 {row['date'].strftime('%Y-%m-%d')}: "
                  f"价格={row['close']:.2f}, 盈利={profit_pct:.2f}%")
            position = 0
            entry_price = 0
    
    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = capital
    
    total_return = (final_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    
    buy_trades = [t for t in trades if t['action'] == 'BUY']
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    wins = [t for t in sell_trades if t.get('profit_pct', 0) > 0]
    
    print(f"\n{'='*50}")
    print(f"{name} - 回测结果（趋势过滤版）")
    print(f"{'='*50}")
    print(f"初始资金: {INITIAL_CAPITAL:.2f}")
    print(f"最终资产: {final_value:.2f}")
    print(f"总收益率: {total_return:.2f}%")
    print(f"买入次数: {len(buy_trades)}")
    print(f"卖出次数: {len(sell_trades)}")
    print(f"跳过震荡: {skipped}次")
    if len(sell_trades) > 0:
        win_rate = len(wins) / len(sell_trades) * 100
        print(f"胜率: {win_rate:.1f}%")
    
    return total_return

# ============== 主程序 ==============
if __name__ == '__main__':
    stocks = [
        ('601318', '中国平安'),
        ('600036', '招商银行'),
        ('600519', '贵州茅台'),
        ('000858', '五粮液'),
    ]
    
    print("="*60)
    print("A股均线策略 v3 - 带趋势/震荡过滤")
    print("="*60)
    print(f"短期均线: {SHORT_WINDOW}日, 长期均线: {LONG_WINDOW}日")
    print(f"ATR周期: {ATR_WINDOW}, ATR倍数: {ATR_MULT}")
    print(f"止损线: {STOP_LOSS_PCT*100}%")
    print("="*60)
    
    for symbol, name in stocks:
        print(f"\n{'='*50}")
        print(f"股票: {name} ({symbol})")
        print(f"{'='*50}")
        
        try:
            df = get_stock_data(symbol, days=500)
            df = calculate_trend_strength(df)
            df = generate_signals(df)
            result = backtest(df, name)
        except Exception as e:
            print(f"错误: {e}")
