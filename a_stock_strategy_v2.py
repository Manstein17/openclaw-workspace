"""
A股均线交叉策略 v2 - 移植自Lean（带止损优化）
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============== 策略参数（可调整） ==============
SHORT_WINDOW = 5    # 短期均线周期（从10改为5）
LONG_WINDOW = 20     # 长期均线周期（从30改为20）
STOP_LOSS_PCT = 0.05  # 止损线：亏损5%自动平仓
INITIAL_CAPITAL = 100000  # 初始资金

# ============== 数据获取 ==============
def get_stock_data(symbol='600519', days=500):
    """获取A股股票历史数据"""
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
        '日期': 'date',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume'
    })
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    return df

# ============== 策略逻辑 ==============
def calculate_ma(df, window):
    return df['close'].rolling(window=window).mean()

def generate_signals(df):
    df['short_ma'] = calculate_ma(df, SHORT_WINDOW)
    df['long_ma'] = calculate_ma(df, LONG_WINDOW)
    df['signal'] = 0
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] <= df['long_ma'], 'signal'] = -1
    df['position'] = df['signal'].diff()
    return df

# ============== 回测引擎（带止损） ==============
def backtest_with_stoploss(df, initial_capital=INITIAL_CAPITAL):
    capital = initial_capital
    position = 0
    entry_price = 0
    trades = []
    stop_loss_triggered = 0
    
    for i, row in df.iterrows():
        if pd.isna(row['position']) or pd.isna(row['close']):
            continue
        
        # 检查止损
        if position > 0:
            loss_pct = (row['close'] - entry_price) / entry_price
            if loss_pct <= -STOP_LOSS_PCT:
                # 触发止损
                revenue = position * row['close']
                capital += revenue
                trades.append({
                    'date': row['date'],
                    'action': 'STOP_LOSS',
                    'price': row['close'],
                    'shares': position,
                    'revenue': revenue,
                    'loss_pct': loss_pct * 100
                })
                print(f"止损 {row['date'].strftime('%Y-%m-%d')}: "
                      f"价格={row['close']:.2f}, 亏损={loss_pct*100:.2f}%")
                position = 0
                entry_price = 0
                stop_loss_triggered += 1
                continue
        
        if position > 0:
            continue
            
        # 买入信号
        if row['position'] == 2 and capital > 0:
            buy_amount = capital * 0.9  # 仓位提高到90%
            shares = int(buy_amount / row['close'])
            if shares > 0:
                cost = shares * row['close']
                capital -= cost
                position = shares
                entry_price = row['close']
                trades.append({
                    'date': row['date'],
                    'action': 'BUY',
                    'price': row['close'],
                    'shares': shares,
                    'cost': cost
                })
                print(f"买入 {row['date'].strftime('%Y-%m-%d')}: "
                      f"价格={row['close']:.2f}, 股数={shares}")
                
        # 卖出信号（死叉且有持仓）
        elif row['position'] == -2 and position > 0:
            revenue = position * row['close']
            capital += revenue
            profit_pct = (row['close'] - entry_price) / entry_price * 100
            trades.append({
                'date': row['date'],
                'action': 'SELL',
                'price': row['close'],
                'shares': position,
                'revenue': revenue,
                'profit_pct': profit_pct
            })
            print(f"卖出 {row['date'].strftime('%Y-%m-%d')}: "
                  f"价格={row['close']:.2f}, 盈利={profit_pct:.2f}%")
            position = 0
            entry_price = 0
    
    # 最终持仓
    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = capital
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    # 统计
    buy_trades = [t for t in trades if t['action'] == 'BUY']
    sell_trades = [t for t in trades if t['action'] == 'SELL']
    wins = [t for t in sell_trades if t.get('profit_pct', 0) > 0]
    
    print(f"\n{'='*50}")
    print(f"回测结果（带止损）")
    print(f"{'='*50}")
    print(f"初始资金: {initial_capital:.2f}")
    print(f"最终资产: {final_value:.2f}")
    print(f"总收益率: {total_return:.2f}%")
    print(f"买入次数: {len(buy_trades)}")
    print(f"卖出次数: {len(sell_trades)}")
    print(f"止损次数: {stop_loss_triggered}")
    print(f"盈利次数: {len(wins)}")
    if len(sell_trades) > 0:
        win_rate = len(wins) / len(sell_trades) * 100
        print(f"胜率: {win_rate:.1f}%")
    
    return {
        'trades': trades,
        'final_value': final_value,
        'total_return': total_return
    }

# ============== 主程序 ==============
if __name__ == '__main__':
    print("="*50)
    print("A股均线交叉策略 v2 - 带止损")
    print("="*50)
    print(f"短期均线: {SHORT_WINDOW}日")
    print(f"长期均线: {LONG_WINDOW}日")
    print(f"止损线: {STOP_LOSS_PCT*100}%")
    print("="*50)
    
    # 测试多只股票
    stocks = [
        ('600519', '贵州茅台'),
        ('000858', '五粮液'),
        ('601318', '中国平安'),
        ('600036', '招商银行'),
    ]
    
    for symbol, name in stocks:
        print(f"\n{'='*50}")
        print(f"股票: {name} ({symbol})")
        print(f"{'='*50}")
        
        try:
            df = get_stock_data(symbol, days=500)
            df = generate_signals(df)
            result = backtest_with_stoploss(df)
        except Exception as e:
            print(f"获取数据失败: {e}")
