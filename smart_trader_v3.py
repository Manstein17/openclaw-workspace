"""
A股智能交易系统 v3 - 完整版
价值投资(财报深度分析) + 技术分析 + 自动策略选择
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============== 配置 ==============
INITIAL_CAPITAL = 10000
MAX_POSITIONS = 3

# 精简股票池（各行业龙头）
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
    ('510300', '沪深300ETF', 'ETF'),
    ('510500', '500ETF', 'ETF'),
]

# ============== 财报深度分析 ==============
def analyze_financials(symbol):
    """
    深度财报分析
    输入: 公司财报数据
    判断标准:
    - ROE > 15% (持续3年以上)
    - 负债率 < 50%
    - 自由现金流 > 净利润的80%
    - 护城河评估
    输出: 投资评级(A/B/C/D) + 理由
    """
    try:
        # 获取主要财务指标
        df = ak.stock_financial_analysis_indicator(symbol=symbol)
        
        if df is None or len(df) == 0:
            return None
        
        # 取最近3年数据
        df = df.head(3) if len(df) >= 3 else df
        
        # 提取关键指标 (列名可能变化，尝试多种)
        def get_val(cols, key):
            for c in cols:
                if key.lower() in c.lower():
                    return c
            return None
        
        # ROE分析
        roe_col = None
        for col in df.columns:
            if '净资产收益率' in col or 'ROE' in col:
                roe_col = col
                break
        
        # 负债率
        debt_col = None
        for col in df.columns:
            if '负债率' in col or '资产负债' in col:
                debt_col = col
                break
        
        # 净利润
        profit_col = None
        for col in df.columns:
            if '净利润' in col and '归属' in col:
                profit_col = col
                break
        
        # 现金流
        cf_col = None
        for col in df.columns:
            if '现金流' in col and '经营' in col:
                cf_col = col
                break
        
        # 计算评分
        scores = {}
        reasons = []
        
        # 1. ROE评分 (0-30分)
        if roe_col:
            roe_values = pd.to_numeric(df[roe_col], errors='coerce').dropna()
            if len(roe_values) > 0:
                avg_roe = roe_values.mean()
                if avg_roe > 15:
                    roe_score = min(30, 30 * (avg_roe / 25))
                    scores['ROE'] = roe_score
                    reasons.append(f"ROE {avg_roe:.1f}% > 15% ✓")
                else:
                    scores['ROE'] = max(0, 15 * (avg_roe / 15))
                    reasons.append(f"ROE {avg_roe:.1f}% < 15% ✗")
        
        # 2. 负债率评分 (0-30分)
        if debt_col:
            debt_values = pd.to_numeric(df[debt_col], errors='coerce').dropna()
            if len(debt_values) > 0:
                avg_debt = debt_values.mean()
                if avg_debt < 50:
                    debt_score = min(30, 30 * (1 - avg_debt / 60))
                    scores['负债率'] = debt_score
                    reasons.append(f"负债率 {avg_debt:.1f}% < 50% ✓")
                else:
                    scores['负债率'] = max(0, 15 * (1 - avg_debt / 100))
                    reasons.append(f"负债率 {avg_debt:.1f}% > 50% ✗")
        
        # 3. 现金流评分 (0-20分) - 需要利润表和现金流表
        scores['现金流'] = 10  # 默认中等
        reasons.append("现金流数据待完善")
        
        # 4. 护城河评分 (0-20分) - 基于行业
        moat_scores = {
            '白酒': 18,   # 品牌护城河强
            '保险': 15,   # 金融牌照
            '银行': 14,   # 牌照+规模
            '医药': 16,   # 研发壁垒
            '新能源': 15, # 技术壁垒
            '新能源车': 14,
            '家电': 12,   # 成本优势
            '电力': 13,   # 垄断
            '消费': 12,
            'ETF': 10,   # 低费率
        }
        
        industry = None
        for name, ind in STOCK_POOL:
            if name == symbol:
                industry = ind
                break
        
        moat_score = moat_scores.get(industry, 10)
        scores['护城河'] = moat_score
        reasons.append(f"行业护城河: {industry}")
        
        # 总分
        total_score = sum(scores.values())
        
        # 评级
        if total_score >= 80:
            rating = 'A'
            verdict = '强烈推荐'
        elif total_score >= 60:
            rating = 'B'
            verdict = '建议买入'
        elif total_score >= 40:
            rating = 'C'
            verdict = '观望'
        else:
            rating = 'D'
            verdict = '不建议'
        
        return {
            'rating': rating,
            'verdict': verdict,
            'score': total_score,
            'details': scores,
            'reasons': reasons
        }
        
    except Exception as e:
        return {
            'rating': 'C',
            'verdict': '数据获取失败',
            'score': 40,
            'error': str(e)
        }

# ============== 实时行情 ==============
def get_realtime_quote(symbol):
    """获取实时报价"""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == symbol]
        if len(row) > 0:
            r = row.iloc[0]
            return {
                'price': float(r['最新价']) if pd.notna(r['最新价']) else 0,
                'change': float(r['涨跌幅']) if pd.notna(r['涨跌幅']) else 0,
                'pe': float(r['市盈率-动态']) if pd.notna(r.get('市盈率-动态')) and r.get('市盈率-动态') != '-' else 999,
                'pb': float(r['市净率']) if pd.notna(r.get('市净率')) and r.get('市净率') != '-' else 999,
                'turnover': float(r['换手率']) if pd.notna(r.get('换手率')) else 0,
            }
    except:
        pass
    return None

# ============== 技术分析策略 ==============
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

STRATEGIES = {
    '均线交叉': ma_crossover,
    'RSI': rsi_strategy,
    'MACD': macd_strategy,
}

# ============== 快速回测 ==============
def quick_backtest(df, strategy_func, days=20):
    if len(df) < 30:
        return None
    
    df = strategy_func(df.copy())
    test_df = df.tail(days).copy()
    
    capital = INITIAL_CAPITAL * 0.3
    position = 0
    entry_price = 0
    wins = 0
    trades = 0
    
    for i, row in test_df.iterrows():
        if pd.isna(row.get('position')):
            continue
        
        if row['position'] == 2 and position == 0 and capital > 0:
            shares = int((capital * 0.9) / row['close'])
            if shares > 0:
                capital -= shares * row['close']
                position = shares
                entry_price = row['close']
        
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
    
    total_return = (final_value - INITIAL_CAPITAL * 0.3) / (INITIAL_CAPITAL * 0.3) * 100
    
    return {
        'return': total_return,
        'trades': trades,
        'win_rate': wins / trades * 100 if trades > 0 else 0
    }

# ============== 综合分析 ==============
def analyze_stock(symbol, name, industry):
    """综合分析一只股票"""
    # 1. 财报分析
    financial = analyze_financials(symbol)
    
    # 2. 实时行情
    quote = get_realtime_quote(symbol)
    
    # 3. 技术分析
    try:
        df = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                start_date=(datetime.now()-timedelta(days=60)).strftime('%Y%m%d'),
                                end_date=datetime.now().strftime('%Y%m%d'),
                                adjust='qfq')
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        })
    except:
        df = None
    
    tech_results = []
    if df is not None:
        for sname, sfunc in STRATEGIES.items():
            result = quick_backtest(df, sfunc, days=15)
            if result:
                tech_results.append({
                    'strategy': sname,
                    'return': result['return'],
                    'win_rate': result['win_rate']
                })
    
    # 找最佳策略
    best_tech = max(tech_results, key=lambda x: x['return']) if tech_results else None
    
    # 综合评分
    fin_score = financial['score'] if financial else 40
    tech_score = best_tech['return'] if best_tech else 0
    
    # 权重: 财报60% + 技术40%
    combined = fin_score * 0.6 + max(0, tech_score + 50) * 0.4
    
    return {
        'symbol': symbol,
        'name': name,
        'industry': industry,
        'quote': quote,
        'financial': financial,
        'best_tech': best_tech,
        'combined_score': combined
    }

# ============== 主程序 ==============
def run_analysis():
    print("="*70)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} A股智能分析系统 v3")
    print("="*70)
    print("分析维度: 财报深度(ROE/负债率/护城河) + 技术面(均线/RSI/MACD)")
    print("="*70)
    
    results = []
    
    for symbol, name, industry in STOCK_POOL:
        print(f"\n分析 {name}...", end=" ")
        
        result = analyze_stock(symbol, name, industry)
        
        if result['financial']:
            rating = result['financial']['rating']
            score = result['financial']['score']
            print(f"财报评级:{rating}({score}分)", end=" ")
        
        if result['best_tech']:
            print(f"技术:{result['best_tech']['strategy']}({result['best_tech']['return']:+.1f}%)", end=" ")
        
        print(f"综合:{result['combined_score']:.1f}")
        
        results.append(result)
    
    # 排序
    results.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # 显示Top5
    print("\n" + "="*70)
    print("📊 综合排名 TOP 5")
    print("="*70)
    
    for i, r in enumerate(results[:5], 1):
        fin = r['financial']
        quote = r['quote']
        tech = r['best_tech']
        
        print(f"\n{i}. {r['name']} ({r['symbol']})")
        print(f"   行业: {r['industry']}")
        
        if quote:
            print(f"   现价: {quote['price']:.2f} ({quote['change']:+.2f}%)")
            print(f"   PE: {quote['pe']:.1f} | PB: {quote['pb']:.2f}")
        
        if fin:
            print(f"   财报评级: {fin['rating']} ({fin['score']}分) - {fin['verdict']}")
            for reason in fin.get('reasons', [])[:3]:
                print(f"      • {reason}")
        
        if tech:
            print(f"   推荐策略: {tech['strategy']} (历史收益:{tech['return']:+.1f}%)")
        
        print(f"   ★ 综合得分: {r['combined_score']:.1f}")
    
    print("\n" + "="*70)
    print("🎯 今日推荐买入")
    print("="*70)
    
    for i, r in enumerate(results[:3], 1):
        if r['quote'] and r['financial']:
            print(f"\n{i}. 买入 {r['name']}")
            print(f"   代码: {r['symbol']}")
            print(f"   价格: {r['quote']['price']:.2f}")
            print(f"   策略: {r['best_tech']['strategy'] if r['best_tech'] else '待定'}")
            print(f"   理由: {r['financial']['verdict']}")

if __name__ == '__main__':
    run_analysis()
