"""
A股均线交叉策略 - 移植自Lean
基于 MovingAverageCrossAlgorithm
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============== 策略参数 ==============
SHORT_WINDOW = 10   # 短期均线周期
LONG_WINDOW = 30    # 长期均线周期
INITIAL_CAPITAL = 100000  # 初始资金

# ============== 数据获取 ==============
def get_stock_data(symbol='600519', days=365):
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
    
    # 整理数据格式
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
    """计算移动平均线"""
    return df['close'].rolling(window=window).mean()

def generate_signals(df):
    """生成交易信号"""
    # 计算均线
    df['short_ma'] = calculate_ma(df, SHORT_WINDOW)
    df['long_ma'] = calculate_ma(df, LONG_WINDOW)
    
    # 初始化信号列
    df['signal'] = 0
    
    # 金叉：短期均线上穿长期均线 -> 买入信号(1)
    # 死叉：短期均线下穿长期均线 -> 卖出信号(-1)
    df.loc[df['short_ma'] > df['long_ma'], 'signal'] = 1
    df.loc[df['short_ma'] <= df['long_ma'], 'signal'] = -1
    
    # 计算持仓信号变化（避免频繁交易）
    df['position'] = df['signal'].diff()
    
    return df

# ============== 回测引擎 ==============
def backtest(df, initial_capital=INITIAL_CAPITAL):
    """简单回测"""
    capital = initial_capital
    position = 0  # 持仓股数
    trades = []
    
    for i, row in df.iterrows():
        if pd.isna(row['position']) or row['position'] == 0:
            continue
            
        # 买入信号
        if row['position'] == 2 and capital > 0:  # 金叉
            # 用80%资金买入
            buy_amount = capital * 0.8
            shares = int(buy_amount / row['close'])
            if shares > 0:
                cost = shares * row['close']
                capital -= cost
                position = shares
                trades.append({
                    'date': row['date'],
                    'action': 'BUY',
                    'price': row['close'],
                    'shares': shares,
                    'cost': cost
                })
                print(f"买入 {row['date'].strftime('%Y-%m-%d')}: "
                      f"价格={row['close']:.2f}, 股数={shares}, 金额={cost:.2f}")
                
        # 卖出信号
        elif row['position'] == -2 and position > 0:  # 死叉
            revenue = position * row['close']
            capital += revenue
            trades.append({
                'date': row['date'],
                'action': 'SELL',
                'price': row['close'],
                'shares': position,
                'revenue': revenue
            })
            print(f"卖出 {row['date'].strftime('%Y-%m-%d')}: "
                  f"价格={row['close']:.2f}, 股数={position}, 金额={revenue:.2f}")
            position = 0
    
    # 计算最终资产
    if position > 0:
        final_value = position * df.iloc[-1]['close']
    else:
        final_value = capital
    
    total_return = (final_value - initial_capital) / initial_capital * 100
    
    print(f"\n{'='*50}")
    print(f"回测结果")
    print(f"{'='*50}")
    print(f"初始资金: {initial_capital:.2f}")
    print(f"最终资产: {final_value:.2f}")
    print(f"总收益率: {total_return:.2f}%")
    print(f"交易次数: {len(trades)}")
    
    return {
        'trades': trades,
        'final_value': final_value,
        'total_return': total_return
    }

# ============== 主程序 ==============
if __name__ == '__main__':
    print("="*50)
    print("A股均线交叉策略 - Lean移植版")
    print("="*50)
    print(f"股票: 贵州茅台(600519)")
    print(f"短期均线: {SHORT_WINDOW}日")
    print(f"长期均线: {LONG_WINDOW}日")
    print("="*50)
    
    # 获取数据
    print("\n获取数据中...")
    df = get_stock_data('600519', days=500)
    print(f"数据范围: {df['date'].min().strftime('%Y-%m-%d')} 至 {df['date'].max().strftime('%Y-%m-%d')}")
    print(f"数据条数: {len(df)}")
    
    # 生成信号
    print("\n计算信号...")
    df = generate_signals(df)
    
    # 回测
    print("\n开始回测...")
    result = backtest(df)
