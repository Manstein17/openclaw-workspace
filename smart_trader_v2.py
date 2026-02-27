"""
A股智能交易系统 v2 - 价值投资 + 策略选择
增强版：基本面分析 + 行业分析 + 策略选择
"""
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# ============== 配置 ==============
INITIAL_CAPITAL = 10000
MAX_POSITIONS = 3
STOP_LOSS_PCT = 0.05
TAKE_PROFIT_PCT = 0.10

# 扩展股票池（加入不同行业）
STOCK_POOL = [
    # 金融
    ('601318', '中国平安', '保险'),
    ('600036', '招商银行', '银行'),
    ('600030', '中信证券', '证券'),
    ('601988', '中国银行', '银行'),
    ('601939', '建设银行', '银行'),
    # 消费
    ('600519', '贵州茅台', '白酒'),
    ('000858', '五粮液', '白酒'),
    ('000333', '美的集团', '家电'),
    ('000651', '格力电器', '家电'),
    # 科技
    ('300750', '宁德时代', '新能源车'),
    ('002594', '比亚迪', '新能源车'),
    ('600276', '恒瑞医药', '医药'),
    ('300015', '爱尔眼科', '医疗'),
    # 周期
    ('600900', '长江电力', '电力'),
    ('601888', '中国中免', '消费'),
    ('600104', '上汽集团', '汽车'),
    # ETF
    ('510300', '沪深300ETF', 'ETF'),
    ('510500', '500ETF', 'ETF'),
    ('159995', '券商ETF', 'ETF'),
]

# ============== 基础数据获取 ==============
def get_realtime_price(symbol):
    """获取实时价格"""
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == symbol]
        if len(row) > 0:
            return float(row.iloc[0]['最新价'])
    except:
        pass
    return None

def get_financial_data(symbol):
    """获取基本面数据"""
    try:
        # 估值数据
        df = ak.stock_zh_a_hist(symbol=symbol, period='daily', 
                                 start_date=(datetime.now()-timedelta(days=5)).strftime('%Y%m%d'),
                                 end_date=datetime.now().strftime('%Y%m%d'),
                                 adjust='qfq')
        
        # 财务指标
        fin = ak.stock_financial_analysis_indicator(symbol=symbol)
        
        return {
            'price': df.iloc[-1]['收盘'] if len(df) > 0 else None,
            'financial': fin,
        }
    except Exception as e:
        return {'error': str(e)}

def get_stock_info(symbol):
    """获取股票基本信息"""
    try:
        df = ak.stock_individual_info_em(symbol=symbol)
        info = {}
        for _, row in df.iterrows():
            info[row['item']] = row['value']
        return info
    except:
        return {}

def get_industry_pe():
    """获取行业PE估值"""
    try:
        df = ak.index_spot_sina()
        return df
    except:
        return None

# ============== 价值投资评分 ==============
def evaluate_stock(symbol, name, industry):
    """综合评估股票价值"""
    try:
        # 获取实时行情
        df = ak.stock_zh_a_spot_em()
        stock_row = df[df['代码'] == symbol]
        
        if len(stock_row) == 0:
            return None
        
        row = stock_row.iloc[0]
        
        # 提取指标
        price = float(row['最新价']) if pd.notna(row['最新价']) else 0
        pe = float(row['市盈率-动态']) if pd.notna(row['市盈率-动态']) and row['市盈率-动态'] != '-' else 999
        pb = float(row['市净率']) if pd.notna(row['市净率']) and row['市净率'] != '-' else 999
        turnover = float(row['换手率']) if pd.notna(row['换手率']) else 0
        
        # 行业PE（申万一级）
        try:
            industry_df = ak.index_spot_sina()
            industry_row = industry_df[industry_df['板块名称'].str.contains(industry, na=False)]
            if len(industry_row) > 0:
                industry_pe = float(industry_row.iloc[0]['涨跌幅'])
            else:
                industry_pe = 0
        except:
            industry_pe = 0
        
        # 价值评分（PE和PB越低越好）
        score = 100
        
        # PE评分（0-30，负PE或>100扣分）
        if pe > 0 and pe < 100:
            pe_score = max(0, 30 - pe / 3)
            score -= pe_score
        
        # PB评分（0-30）
        if pb > 0 and pb < 20:
            pb_score = max(0, 30 - pb * 2)
            score -= pb_score
        
        # 换手率评分（0-20，换手太高可能过热）
        if turnover > 5:
            score -= min(20, (turnover - 5))
        
        # 行业趋势加分/减分（0-20）
        score += industry_pe * 2  # 行业涨跌幅影响
        
        return {
            'symbol': symbol,
            'name': name,
            'industry': industry,
            'price': price,
            'pe': pe,
            'pb': pb,
            'turnover': turnover,
            'industry_trend': industry_pe,
            'value_score': max(0, min(100, score)),
            'recommendation': '买入' if score > 60 else ('持有' if score > 40 else '观望')
        }
    except Exception as e:
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

# ============== 回测 ==============
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
        'wins': wins,
        'win_rate': wins / trades * 100 if trades > 0 else 0
    }

# ============== 综合分析 ==============
def comprehensive_analysis():
    """综合价值投资 + 技术分析"""
    print("="*70)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} 全市场扫描")
    print("="*70)
    
    opportunities = []
    
    for symbol, name, industry in STOCK_POOL:
        print(f"分析: {name}...", end=" ")
        
        # 1. 价值评估
        value = evaluate_stock(symbol, name, industry)
        
        if value is None:
            print("数据获取失败")
            continue
        
        # 2. 获取历史数据做技术分析
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                    start_date=(datetime.now()-timedelta(days=90)).strftime('%Y%m%d'),
                                    end_date=datetime.now().strftime('%Y%m%d'),
                                    adjust='qfq')
            df = df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            })
        except:
            print("历史数据获取失败")
            continue
        
        # 3. 测试各策略
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
        
        if best_strategy:
            opportunities.append({
                'symbol': symbol,
                'name': name,
                'industry': industry,
                'value': value,
                'strategy': best_strategy,
                'combined_score': value['value_score'] * 0.4 + max(0, best_return) * 0.6
            })
            print(f"✓ 价值:{value['value_score']:.0f} 技术:{best_return:+.1f}%")
    
    # 排序
    opportunities.sort(key=lambda x: x['combined_score'], reverse=True)
    
    return opportunities

# ============== 显示结果 ==============
def show_recommendations(opportunities, top_n=5):
    print("\n" + "="*70)
    print("📊 综合分析排名 TOP {}".format(top_n))
    print("="*70)
    
    for i, opp in enumerate(opportunities[:top_n], 1):
        v = opp['value']
        s = opp['strategy']
        
        print(f"\n{i}. {v['name']} ({v['symbol']})")
        print(f"   行业: {v['industry']} | 价格: {v['price']:.2f}")
        print(f"   市盈率: {v['pe']:.1f} | 市净率: {v['pb']:.2f}")
        print(f"   换手率: {v['turnover']:.1f}%")
        print(f"   价值评分: {v['value_score']:.0f}/100 [{v['recommendation']}]")
        print(f"   技术策略: {s['name']} | 历史收益: {s['return']:+.1f}% | 胜率: {s['win_rate']:.0f}%")
        print(f"   综合评分: {opp['combined_score']:.1f}")
    
    return opportunities[:top_n]

# ============== 主程序 ==============
if __name__ == '__main__':
    opportunities = comprehensive_analysis()
    recommendations = show_recommendations(opportunities, top_n=5)
    
    print("\n" + "="*70)
    print("🎯 今日推荐交易")
    print("="*70)
    
    # 推荐前3只
    for i, rec in enumerate(recommendations[:3], 1):
        v = rec['value']
        s = rec['strategy']
        
        print(f"\n{i}. 买入 {v['name']}")
        print(f"   代码: {v['symbol']}")
        print(f"   价格: {v['price']:.2f}")
        print(f"   策略: {s['name']}")
        print(f"   理由: {v['recommendation']} + {s['name']}")
        print(f"   预期收益: {s['return']:+.1f}%")
