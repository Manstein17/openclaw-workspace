"""
A股数据缓存系统
- 首次下载全部历史数据
- 每日增量更新
- 本地读取，速度快
"""
import akshare as ak
import pandas as pd
import os
from datetime import datetime, timedelta

# 配置
CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_cache")
DAILY_DIR = os.path.join(CACHE_DIR, "daily")
os.makedirs(DAILY_DIR, exist_ok=True)

# 精简股票池（各行业龙头）
STOCK_POOL = [
    ('601318', '中国平安'),
    ('600036', '招商银行'),
    ('600519', '贵州茅台'),
    ('000858', '五粮液'),
    ('300750', '宁德时代'),
    ('002594', '比亚迪'),
    ('600276', '恒瑞医药'),
    ('000333', '美的集团'),
    ('600900', '长江电力'),
    ('601888', '中国中免'),
    ('510300', '沪深300ETF'),
    ('510500', '500ETF'),
]

def get_cache_path(symbol):
    """获取缓存文件路径"""
    return os.path.join(DAILY_DIR, f"{symbol}.csv")

def is_cache_valid(symbol, days=30):
    """检查缓存是否有效"""
    path = get_cache_path(symbol)
    if not os.path.exists(path):
        return False
    
    # 检查文件更新时间
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    age = datetime.now() - mtime
    
    # 盘中(9:30-15:00)需要当天数据，盘后可以用昨天的
    now = datetime.now()
    is_trading_hours = (now.hour >= 9 and now.hour < 15)
    
    if is_trading_hours:
        return age.seconds < 300  # 5分钟内有效
    else:
        return age.days < 1  # 1天内有效

def download_stock_data(symbol, years=3):
    """下载股票历史数据"""
    print(f"下载 {symbol}...", end=" ")
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y%m%d')
    
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        # 整理格式
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('date').reset_index(drop=True)
        
        # 保存
        path = get_cache_path(symbol)
        df.to_csv(path, index=False)
        
        print(f"✓ {len(df)}条数据")
        return df
    except Exception as e:
        print(f"✗ 错误: {e}")
        return None

def update_stock_data(symbol):
    """增量更新数据"""
    path = get_cache_path(symbol)
    
    if not os.path.exists(path):
        return download_stock_data(symbol)
    
    # 读取现有数据
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    last_date = df['date'].max()
    
    # 获取新数据
    start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
    end_date = datetime.now().strftime('%Y%m%d')
    
    if start_date >= end_date:
        print(f"{symbol}: 无新数据")
        return df
    
    print(f"更新 {symbol}...", end=" ")
    
    try:
        new_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )
        
        if len(new_df) > 0:
            new_df = new_df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume'
            })
            new_df['date'] = pd.to_datetime(new_df['date'])
            new_df = new_df[['date', 'open', 'high', 'low', 'close', 'volume']]
            
            # 合并
            df = pd.concat([df, new_df], ignore_index=True)
            df = df.drop_duplicates(subset=['date']).sort_values('date')
            
            # 保存
            df.to_csv(path, index=False)
            print(f"+{len(new_df)}条")
        else:
            print("无新数据")
        
        return df
    except Exception as e:
        print(f"错误: {e}")
        return df

def get_cached_data(symbol):
    """从缓存读取数据"""
    path = get_cache_path(symbol)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    return None

def init_cache():
    """初始化缓存（首次运行）"""
    print("="*60)
    print("初始化数据缓存")
    print("="*60)
    
    # 检查已缓存
    cached = []
    for symbol, _ in STOCK_POOL:
        path = get_cache_path(symbol)
        if os.path.exists(path):
            cached.append(symbol)
    
    print(f"已有缓存: {len(cached)}只")
    
    # 下载缺失的
    for symbol, name in STOCK_POOL:
        if symbol not in cached:
            download_stock_data(symbol)

def update_cache():
    """更新缓存（每日运行）"""
    print("="*60)
    print("增量更新缓存")
    print("="*60)
    
    for symbol, name in STOCK_POOL:
        update_stock_data(symbol)

def get_realtime_simple():
    """快速获取实时行情（单次请求）"""
    try:
        df = ak.stock_zh_a_spot_em()
        return df
    except:
        return None

# ============== 快速分析（使用缓存） ==============
def quick_analysis():
    """使用缓存快速分析"""
    print("\n" + "="*60)
    print("📊 快速分析（缓存模式）")
    print("="*60)
    
    import numpy as np
    
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
        df['signal'] = np.where(df['rsi'] < 30, 1, np.where(df['rsi'] > 70, -1, 0))
        df['position'] = df['signal'].diff()
        return df
    
    results = []
    
    for symbol, name in STOCK_POOL:
        df = get_cached_data(symbol)
        
        if df is None or len(df) < 30:
            continue
        
        # 简单回测
        df = ma_crossover(df.copy())
        test = df.tail(20)
        
        # 简单信号
        last = df.iloc[-1] if len(df) > 0 else None
        
        if last is not None:
            signal = "买入" if last['ma5'] > last['ma10'] else "观望"
            price = last['close']
            
            results.append({
                'symbol': symbol,
                'name': name,
                'price': price,
                'signal': signal,
                'ma5': last['ma5'],
                'ma10': last['ma10']
            })
    
    # 显示
    print("\n今日信号:")
    for r in results:
        print(f"  {r['name']:10s} {r['symbol']:6s} 现价:{r['price']:8.2f} 信号:{r['signal']}")
    
    return results

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'init':
            init_cache()
        elif cmd == 'update':
            update_cache()
        elif cmd == 'analyze':
            quick_analysis()
    else:
        # 默认：检查缓存有效性，缺失则下载
        init_cache()
        quick_analysis()
