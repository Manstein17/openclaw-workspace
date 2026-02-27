"""
A股每日模拟交易系统 v5
- 每日收盘后分析
- 第二天模拟执行
- 记录每日收益
- 持续优化改进
"""
import akshare as ak
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta

# ============== 配置 ==============
INITIAL_CAPITAL = 10000  # 初始1万
MAX_POSITIONS = 3         # 最多持仓3只
STOP_LOSS_PCT = 0.05     # 5%止损
TAKE_PROFIT_PCT = 0.10   # 10%止盈

CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_cache/daily")
STATE_FILE = os.path.expanduser("~/.openclaw/workspace/trading_state.json")

# 股票池（精简到10只）
STOCK_POOL = [
    ('601318', '中国平安', '保险', 8, 15),
    ('600036', '招商银行', '银行', 5, 10),
    ('600519', '贵州茅台', '白酒', 20, 40),
    ('000858', '五粮液', '白酒', 15, 35),
    ('300750', '宁德时代', '新能源', 15, 30),
    ('002594', '比亚迪', '新能源车', 20, 40),
    ('600276', '恒瑞医药', '医药', 20, 40),
    ('000333', '美的集团', '家电', 10, 20),
    ('600900', '长江电力', '电力', 10, 20),
    ('601888', '中国中免', '消费', 15, 30),
]

# ============== 缓存读取 ==============
def get_cached_data(symbol):
    path = os.path.join(CACHE_DIR, f"{symbol}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return None

# ============== 价格获取（用缓存） ==============
def get_price(symbol):
    """获取价格（用缓存）"""
    df = get_cached_data(symbol)
    if df is not None and len(df) > 0:
        return df.iloc[-1]['close']
    return None

# ============== 技术策略 ==============
def ma_cross(df):
    df = df.copy()
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['signal'] = np.where(df['ma5'] > df['ma10'], 1, -1)
    df['position'] = df['signal'].diff()
    return df

def rsi(df):
    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-10)))
    df['signal'] = np.where(df['rsi'] < 30, 1, np.where(df['rsi'] > 70, -1, 0))
    df['position'] = df['signal'].diff()
    return df

def macd(df):
    df = df.copy()
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['histogram'] = df['macd'] - df['signal_line']
    df['signal'] = np.where(df['histogram'] > 0, 1, -1)
    df['position'] = df['signal'].diff()
    return df

STRATEGIES = {
    'MA': ma_cross,
    'RSI': rsi,
    'MACD': macd
}

# ============== 回测 ==============
def backtest(df, strategy_func, days=20):
    if len(df) < 30:
        return None
    
    df = strategy_func(df)
    test = df.tail(days)
    
    capital = INITIAL_CAPITAL * 0.3
    position = 0
    entry = 0
    wins = 0
    trades = 0
    
    for _, row in test.iterrows():
        if pd.isna(row.get('position')) or row.get('position') == 0:
            continue
        
        # 买入
        if row['position'] == 2 and position == 0 and capital > 0:
            shares = int((capital * 0.9) / row['close'])
            if shares > 0:
                capital -= shares * row['close']
                position = shares
                entry = row['close']
        
        # 卖出
        elif (row['position'] == -2 or row['position'] == -1) and position > 0:
            profit = (row['close'] - entry) / entry
            if profit > 0:
                wins += 1
            trades += 1
            capital += position * row['close']
            position = 0
    
    if position > 0:
        final = capital + position * test.iloc[-1]['close']
    else:
        final = capital
    
    return_pct = (final - INITIAL_CAPITAL * 0.3) / (INITIAL_CAPITAL * 0.3) * 100
    
    return {
        'return': return_pct,
        'trades': trades,
        'wins': wins,
        'win_rate': wins / trades * 100 if trades > 0 else 0
    }

# ============== 综合分析 ==============
def analyze_all():
    """分析所有股票"""
    results = []
    
    for symbol, name, industry, pe_low, pe_high in STOCK_POOL:
        df = get_cached_data(symbol)
        
        if df is None or len(df) < 30:
            continue
        
        # 获取当前价格
        last = df.iloc[-1]
        price = last['close']
        
        # 技术分析
        best_strategy = None
        best_return = -999
        
        for sname, sfunc in STRATEGIES.items():
            result = backtest(df.copy(), sfunc, days=20)
            if result and result['return'] > best_return:
                best_return = result['return']
                best_strategy = {
                    'name': sname,
                    'return': result['return'],
                    'win_rate': result['win_rate']
                }
        
        # 简单估值（基于行业PE区间）
        # 使用最近PE（如果有）
        pe = pe_low + 5  # 默认中间值
        
        if price < pe_high:
            value_score = 30
            value_status = '低估'
        elif price < pe_high * 1.3:
            value_score = 20
            value_status = '合理'
        else:
            value_score = 10
            value_status = '高估'
        
        # 护城河
        moat_scores = {'保险': 15, '银行': 14, '白酒': 18, '医药': 16,
                       '新能源': 15, '新能源车': 14, '家电': 12, '电力': 13, '消费': 12}
        moat = moat_scores.get(industry, 10)
        
        # 综合评分
        fin_score = value_score + moat
        tech_score = best_return + 50 if best_return > -50 else 0
        combined = fin_score * 0.4 + max(0, tech_score) * 0.6
        
        results.append({
            'symbol': symbol,
            'name': name,
            'price': price,
            'value': value_status,
            'value_score': value_score,
            'moat': moat,
            'strategy': best_strategy,
            'combined': combined
        })
    
    # 排序
    results.sort(key=lambda x: x['combined'], reverse=True)
    return results

# ============== 交易状态管理 ==============
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'cash': INITIAL_CAPITAL,
        'positions': {},
        'history': [],
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'total_value': INITIAL_CAPITAL
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_positions(state):
    """检查持仓是否需要止损/止盈"""
    to_sell = []
    
    for symbol, pos in state['positions'].items():
        # 获取当前价格
        price = get_price(symbol)
        if price is None:
            price = pos['entry']  # 用买入价
        
        profit_pct = (price - pos['entry']) / pos['entry']
        
        # 止损
        if profit_pct <= -STOP_LOSS_PCT:
            to_sell.append((symbol, '止损', profit_pct))
        # 止盈
        elif profit_pct >= TAKE_PROFIT_PCT:
            to_sell.append((symbol, '止盈', profit_pct))
    
    return to_sell

# ============== 执行交易 ==============
def execute_trades(state, recommendations):
    """执行买入推荐"""
    for rec in recommendations[:MAX_POSITIONS]:
        if len(state['positions']) >= MAX_POSITIONS:
            break
        
        symbol = rec['symbol']
        if symbol in state['positions']:
            continue
        
        price = get_price(symbol)
        if price is None:
            price = rec['price']
        
        # 买入
        amount = state['cash'] * 0.3
        shares = int(amount / price)
        
        if shares > 0:
            cost = shares * price
            state['cash'] -= cost
            state['positions'][symbol] = {
                'name': rec['name'],
                'shares': shares,
                'entry': price,
                'strategy': rec['strategy']['name'],
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            print(f"📈 买入 {rec['name']} @ {price:.2f} x{shares}")

# ============== 主程序 ==============
def run_daily():
    print("\n" + "="*70)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} 每日交易系统")
    print("="*70)
    
    # 加载状态
    state = load_state()
    
    print(f"\n📊 当前状态")
    print(f"   现金: {state['cash']:.2f}")
    print(f"   持仓数: {len(state['positions'])}")
    print(f"   总资产: {state.get('total_value', state['cash']):.2f}")
    
    # 检查持仓
    to_sell = check_positions(state)
    if to_sell:
        print(f"\n⚠️  需要卖出:")
        for symbol, reason, profit in to_sell:
            pos = state['positions'][symbol]
            price = get_price(symbol) or pos['entry']
            revenue = pos['shares'] * price
            state['cash'] += revenue
            
            profit_pct = profit * 100
            print(f"   {pos['name']} ({reason}, {profit_pct:+.1f}%)")
            
            state['history'].append({
                'symbol': symbol,
                'name': pos['name'],
                'action': 'SELL',
                'price': price,
                'profit_pct': profit_pct,
                'date': datetime.now().strftime('%Y-%m-%d')
            })
            
            del state['positions'][symbol]
    
    # 分析
    print("\n🔍 分析市场...")
    results = analyze_all()
    
    # 显示Top5
    print("\n📈 TOP 5 推荐:")
    for i, r in enumerate(results[:5], 1):
        s = r['strategy']
        print(f"   {i}. {r['name']:8s} {r['symbol']:6s} "
              f"现价:{r['price']:7.2f} 价值:{r['value']} 技术:{s['name']}({s['return']:+.1f}%) "
              f"综合:{r['combined']:.1f}")
    
    # 执行买入
    print("\n🎯 今日交易:")
    recommendations = [r for r in results if r['symbol'] not in state['positions']]
    execute_trades(state, recommendations)
    
    # 计算总资产
    total = state['cash']
    for symbol, pos in state['positions'].items():
        price = get_price(symbol) or pos['entry']
        total += pos['shares'] * price
    
    state['total_value'] = total
    
    # 保存
    save_state(state)
    
    # 最终报告
    print("\n" + "="*70)
    print("📊 每日报告")
    print("="*70)
    print(f"日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"现金: {state['cash']:.2f}")
    print(f"持仓: {len(state['positions'])}只")
    
    for symbol, pos in state['positions'].items():
        price = get_price(symbol) or pos['entry']
        profit = (price - pos['entry']) / pos['entry'] * 100
        print(f"   {pos['name']}: 买入{pos['entry']:.2f} → 当前{price:.2f} ({profit:+.1f}%)")
    
    print(f"\n💰 总资产: {total:.2f}")
    print(f"📈 收益率: {(total - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100:+.2f}%")
    print(f"🏆 历史交易: {len(state['history'])}次")
    
    return state

if __name__ == '__main__':
    run_daily()
