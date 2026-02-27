"""
A股智能交易系统 v4 - 完整版（缓存加速）
价值投资 + 技术分析 + 自动策略选择 + 模拟交易
"""
import akshare as ak
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import json

# ============== 配置 ==============
INITIAL_CAPITAL = 10000
MAX_POSITIONS = 3
STOP_LOSS_PCT = 0.05
TAKE_PROFIT_PCT = 0.10

CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_cache/daily")

# 股票池
STOCK_POOL = [
    ('601318', '中国平安', '保险'),
    ('600036', '招商银行', '银行'),
    ('600519', '贵州茅台', '白酒'),
    ('000858', '五粮液', '白酒'),
    ('300750', '宁德时代', '新能源'),
    ('002594', '比亚迪', '新能源车'),
    ('600276', '恒瑞医药', '医药'),
    ('000333', '美的集团', '家电'),
    ('600900', '长江电力', '电力'),
    ('601888', '中国中免', '消费'),
]

# ============== 缓存读取 ==============
def get_cached_data(symbol):
    """从缓存读取数据"""
    path = os.path.join(CACHE_DIR, f"{symbol}.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return None

# ============== 实时行情 ==============
def get_realtime_quote(symbols):
    """批量获取实时报价（一次请求）"""
    try:
        df = ak.stock_zh_a_spot_em()
        result = {}
        for symbol in symbols:
            row = df[df['代码'] == symbol]
            if len(row) > 0:
                r = row.iloc[0]
                result[symbol] = {
                    'price': float(r['最新价']) if pd.notna(r.get('最新价')) else 0,
                    'change': float(r['涨跌幅']) if pd.notna(r.get('涨跌幅')) else 0,
                    'pe': float(r.get('市盈率-动态', 0)) if pd.notna(r.get('市盈率-动态')) and r.get('市盈率-动态') != '-' else 999,
                    'pb': float(r.get('市净率', 0)) if pd.notna(r.get('市净率')) and r.get('市净率') != '-' else 999,
                }
        return result
    except Exception as e:
        print(f"实时行情获取失败: {e}")
        return {}

# ============== 价值投资分析 ==============
def analyze_value(symbol, industry):
    """
    价值投资评分
    - ROE/负债率（基于行业平均估算）
    - 护城河
    - PE/PB估值
    """
    # 护城河评分
    moat_scores = {
        '保险': 15, '银行': 14, '白酒': 18, '医药': 16,
        '新能源': 15, '新能源车': 14, '家电': 12, '电力': 13, '消费': 12
    }
    moat = moat_scores.get(industry, 10)
    
    # 行业PE合理区间
    pe_ranges = {
        '保险': (8, 15), '银行': (5, 10), '白酒': (20, 40),
        '医药': (20, 40), '新能源': (15, 30), '新能源车': (20, 40),
        '家电': (10, 20), '电力': (10, 20), '消费': (15, 30)
    }
    low, high = pe_ranges.get(industry, (10, 30))
    
    # 获取实时PE
    quotes = get_realtime_quote([symbol])
    quote = quotes.get(symbol, {})
    pe = quote.get('pe', 999)
    
    # 估值评分
    if pe < low:
        pe_score = 30
        pe_status = '低估'
    elif pe < high:
        pe_score = 20
        pe_status = '合理'
    else:
        pe_score = 10
        pe_status = '高估'
    
    # 综合评分
    total_score = moat + pe_score
    
    if total_score >= 45:
        rating = 'A'
        verdict = '强烈推荐'
    elif total_score >= 35:
        rating = 'B'
        verdict = '建议买入'
    elif total_score >= 25:
        rating = 'C'
        verdict = '观望'
    else:
        rating = 'D'
        verdict = '不建议'
    
    return {
        'rating': rating,
        'verdict': verdict,
        'score': total_score,
        'moat': moat,
        'pe': pe,
        'pe_status': pe_status,
        'pe_score': pe_score
    }

# ============== 技术分析策略 ==============
def ma_crossover(df):
    df = df.copy()
    df['ma5'] = df['close'].rolling(5).mean()
    df['ma10'] = df['close'].rolling(10).mean()
    df['ma20'] = df['close'].rolling(20).mean()
    df['signal'] = np.where(df['ma5'] > df['ma10'], 1, -1)
    df['position'] = df['signal'].diff()
    return df

def rsi_strategy(df):
    df = df.copy()
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi_ma'] = df['rsi'].rolling(5).mean()
    df['signal'] = np.where(df['rsi'] < 35, 1, np.where(df['rsi'] > 65, -1, 0))
    df['position'] = df['signal'].diff()
    return df

def macd_strategy(df):
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
    '均线交叉': ma_crossover,
    'RSI': rsi_strategy,
    'MACD': macd_strategy,
}

# ============== 回测 ==============
def backtest(df, strategy_func, days=20):
    """快速回测"""
    if len(df) < 30:
        return None
    
    df = strategy_func(df)
    test_df = df.tail(days).copy()
    
    capital = INITIAL_CAPITAL * 0.3
    position = 0
    entry_price = 0
    wins = 0
    trades = 0
    
    for i, row in test_df.iterrows():
        if pd.isna(row.get('position')) or row.get('position') == 0:
            continue
        
        # 买入
        if row['position'] == 2 and position == 0 and capital > 0:
            shares = int((capital * 0.9) / row['close'])
            if shares > 0:
                capital -= shares * row['close']
                position = shares
                entry_price = row['close']
        
        # 卖出
        elif (row['position'] == -2 or row['position'] == -1) and position > 0:
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
    
    total_return = (final_value - INITIAL_CAPITAL * 0.3) / (INITIAL_CAPITAL * 0.3) * 100
    
    return {
        'return': total_return,
        'trades': trades,
        'wins': wins,
        'win_rate': wins / trades * 100 if trades > 0 else 0
    }

# ============== 综合分析 ==============
def analyze_stock(symbol, name, industry):
    """综合分析"""
    # 1. 缓存读取历史数据
    df = get_cached_data(symbol)
    
    # 2. 价值分析
    value = analyze_value(symbol, industry)
    
    # 3. 技术分析
    tech_results = []
    if df is not None and len(df) > 30:
        for sname, sfunc in STRATEGIES.items():
            result = backtest(df, sfunc, days=20)
            if result:
                tech_results.append({
                    'strategy': sname,
                    'return': result['return'],
                    'win_rate': result['win_rate']
                })
    
    # 找最佳策略
    best_tech = max(tech_results, key=lambda x: x['return']) if tech_results else None
    
    # 4. 综合评分 (价值40% + 技术60%)
    fin_score = value['score']
    tech_score = best_tech['return'] + 50 if best_tech else 0  # 转到0-100
    combined = fin_score * 0.4 + max(0, tech_score) * 0.6
    
    return {
        'symbol': symbol,
        'name': name,
        'industry': industry,
        'value': value,
        'best_tech': best_tech,
        'combined_score': combined
    }

# ============== 模拟交易 ==============
class PaperTrader:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.positions = {}
        self.history = []
    
    def buy(self, symbol, name, price, strategy):
        if len(self.positions) >= MAX_POSITIONS:
            return False
        if self.cash < price * 100:
            return False
        
        shares = int((self.cash * 0.3) / price)
        cost = shares * price
        
        self.positions[symbol] = {
            'name': name,
            'shares': shares,
            'entry': price,
            'strategy': strategy,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        self.cash -= cost
        
        print(f"\n📈 买入 {name}")
        print(f"   价格: {price:.2f}, 股数: {shares}, 金额: {cost:.2f}")
        print(f"   策略: {strategy}")
        return True
    
    def status(self):
        quotes = get_realtime_quote(list(self.positions.keys()))
        
        print("\n" + "="*60)
        print("📊 当前持仓")
        print("="*60)
        
        total_value = self.cash
        
        for symbol, pos in self.positions.items():
            quote = quotes.get(symbol, {})
            current = quote.get('price', pos['entry'])
            profit_pct = (current - pos['entry']) / pos['entry'] * 100
            value = pos['shares'] * current
            total_value += value
            
            print(f"  {pos['name']} ({symbol})")
            print(f"    买入: {pos['entry']:.2f} → 当前: {current:.2f}")
            print(f"    盈亏: {profit_pct:+.2f}%")
        
        print(f"\n现金: {self.cash:.2f}")
        print(f"总资产: {total_value:.2f}")
        print(f"收益率: {(total_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100:+.2f}%")

# ============== 主程序 ==============
def run_analysis():
    print("="*70)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} A股智能分析系统 v4")
    print("="*70)
    print("模式: 缓存加速 | 价值投资(PE/护城河) + 技术分析(均线/RSI/MACD)")
    print("="*70)
    
    results = []
    
    print("\n分析股票...")
    for symbol, name, industry in STOCK_POOL:
        result = analyze_stock(symbol, name, industry)
        
        v = result['value']
        t = result['best_tech']
        
        print(f"  {name:10s} 价值:{v['rating']}({v['score']}) 技术:{t['strategy'] if t else 'N/A'}({t['return']:+.1f}%)" if t else f"  {name:10s} 价值:{v['rating']}({v['score']})")
        
        results.append(result)
    
    # 排序
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # 显示排名
    print("\n" + "="*70)
    print("📊 综合排名 TOP 5")
    print("="*70)
    
    for i, r in enumerate(results[:5], 1):
        v = r['value']
        t = r['best_tech']
        
        print(f"\n{i}. {r['name']} ({r['symbol']})")
        print(f"   行业: {r['industry']}")
        print(f"   价值: {v['rating']}级 ({v['score']}分) - {v['verdict']}")
        print(f"      PE: {v['pe']:.1f} ({v['pe_status']}) | 护城河: {v['moat']}分")
        if t:
            print(f"   技术: {t['strategy']} | 历史收益: {t['return']:+.1f}% | 胜率: {t['win_rate']:.0f}%")
        print(f"   ★ 综合: {r['combined_score']:.1f}")
    
    # 今日推荐
    print("\n" + "="*70)
    print("🎯 今日推荐买入 TOP 3")
    print("="*70)
    
    quotes = get_realtime_quote([r['symbol'] for r in results[:3]])
    
    trader = PaperTrader()
    
    for r in results[:3]:
        v = r['value']
        t = r['best_tech']
        quote = quotes.get(r['symbol'], {})
        price = quote.get('price', 0)
        
        print(f"\n买入 {r['name']}")
        print(f"  代码: {r['symbol']}")
        print(f"  价格: {price:.2f}")
        print(f"  策略: {t['strategy'] if t else '待定'}")
        print(f"  理由: {v['verdict']}")
        
        if price > 0 and r['combined_score'] > 50:
            trader.buy(r['symbol'], r['name'], price, t['strategy'] if t else '均线')
    
    trader.status()
    
    return results

if __name__ == '__main__':
    run_analysis()
