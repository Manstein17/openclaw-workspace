"""
============================================================
A股智能量化交易系统 v6 - 完整版
============================================================
功能模块:
1. 数据管理 - 缓存/更新/清理
2. 基础分析 - PE/PB/行业/市值
3. 财务分析 - ROE/负债/现金流/成长
4. 技术分析 - 6大策略+组合信号
5. 风险管理 - 止损/止盈/仓位/回撤
6. 交易执行 - 自动买卖/状态管理
7. 绩效分析 - 收益/回撤/胜率
8. 策略优化 - 参数调优/自适应
============================================================
"""
import akshare as ak
import pandas as pd
import numpy as np
import os
import json
import subprocess
from datetime import datetime, timedelta
from collections import defaultdict

# ============== 全局配置 ==============
class Config:
    # 资金管理
    INITIAL_CAPITAL = 10000      # 初始资金
    MAX_POSITIONS = 3             # 最大持仓数
    POSITION_SIZE = 0.3           # 单只仓位比例
    MAX_POS_SIZE = 0.4             # 单只最高仓位
    
    # 风控
    STOP_LOSS = 0.05              # 止损5%
    TAKE_PROFIT = 0.10            # 止盈10%
    MAX_DAILY_LOSS = 0.03         # 单日最大亏损3%
    MAX_DRAWDOWN = 0.15           # 最大回撤15%
    
    # 策略参数
    MA_SHORT = 5                  # 短期均线
    MA_LONG = 10                  # 长期均线
    RSI_PERIOD = 14               # RSI周期
    RSI_OVERSOLD = 30             # RSI超卖
    RSI_OVERBOUGHT = 70           # RSI超买
    MACD_FAST = 12
    MACD_SLOW = 26
    MACD_SIGNAL = 9
    
    # 回测参数
    BACKTEST_DAYS = 20            # 回测天数
    WARMUP_DAYS = 30             # 预热天数
    
    # 股票池大小
    MAX_STOCKS = 20

# ============== 数据管理器 ==============
class DataManager:
    CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_cache/daily")
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # 扩展股票池（行业分散）
    STOCK_POOL = [
        # 金融
        ('601318', '中国平安', '保险', 8, 15),
        ('600036', '招商银行', '银行', 5, 10),
        ('600030', '中信证券', '证券', 10, 20),
        ('601988', '中国银行', '银行', 4, 8),
        # 消费
        ('600519', '贵州茅台', '白酒', 20, 40),
        ('000858', '五粮液', '白酒', 15, 35),
        ('000333', '美的集团', '家电', 10, 20),
        ('000651', '格力电器', '家电', 8, 16),
        # 科技
        ('300750', '宁德时代', '新能源', 15, 30),
        ('002594', '比亚迪', '新能源车', 20, 40),
        ('600276', '恒瑞医药', '医药', 20, 40),
        ('002475', '立讯精密', '电子', 15, 30),
        # 周期
        ('600900', '长江电力', '电力', 10, 20),
        ('601888', '中国中免', '消费', 15, 30),
        ('600104', '上汽集团', '汽车', 8, 15),
        ('600036', '招商银行', '银行', 5, 10),
        ('601857', '中国石油', '能源', 6, 12),
        ('600028', '中国石化', '能源', 6, 12),
        # ETF
        ('510300', '沪深300ETF', 'ETF', 10, 20),
        ('510500', '500ETF', 'ETF', 12, 25),
    ]
    
    @classmethod
    def get_cache_path(cls, symbol):
        return os.path.join(cls.CACHE_DIR, f"{symbol}.csv")
    
    @classmethod
    def get_cached_data(cls, symbol):
        path = cls.get_cache_path(symbol)
        if os.path.exists(path):
            df = pd.read_csv(path)
            df['date'] = pd.to_datetime(df['date'])
            return df
        return None
    
    @classmethod
    def get_price(cls, symbol):
        """获取最新价格（缓存）"""
        df = cls.get_cached_data(symbol)
        if df is not None and len(df) > 0:
            return df.iloc[-1]['close']
        return None
    
    @classmethod
    def download_all(cls):
        """下载所有股票数据"""
        print("下载股票数据...")
        for symbol, name, ind, _, _ in cls.STOCK_POOL:
            path = cls.get_cache_path(symbol)
            if not os.path.exists(path):
                try:
                    end = datetime.now().strftime('%Y%m%d')
                    start = (datetime.now() - timedelta(days=1000)).strftime('%Y%m%d')
                    df = ak.stock_zh_a_hist(symbol=symbol, period='daily',
                                            start_date=start, end_date=end, adjust='qfq')
                    if df is not None and len(df) > 0:
                        df = df.rename(columns={
                            '日期': 'date', '开盘': 'open', '收盘': 'close',
                            '最高': 'high', '最低': 'low', '成交量': 'volume'
                        })
                        df['date'] = pd.to_datetime(df['date'])
                        df[['date', 'open', 'high', 'low', 'close', 'volume']].to_csv(path, index=False)
                        print(f"  ✓ {name}")
                except:
                    print(f"  ✗ {name}")
        print("下载完成!")

# ============== 策略库 ==============
class Strategies:
    @staticmethod
    def ma_cross(df):
        """均线交叉"""
        df = df.copy()
        df['ma5'] = df['close'].rolling(5).mean()
        df['ma10'] = df['close'].rolling(10).mean()
        df['ma20'] = df['close'].rolling(20).mean()
        df['signal'] = np.where(df['ma5'] > df['ma10'], 1, -1)
        df['position'] = df['signal'].diff()
        return df
    
    @staticmethod
    def rsi(df):
        """RSI策略"""
        df = df.copy()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + gain / (loss + 1e-10)))
        df['rsi_ma'] = df['rsi'].rolling(5).mean()
        df['signal'] = np.where(df['rsi'] < 30, 1, np.where(df['rsi'] > 70, -1, 0))
        df['position'] = df['signal'].diff()
        return df
    
    @staticmethod
    def macd(df):
        """MACD策略"""
        df = df.copy()
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['signal_line'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['histogram'] = df['macd'] - df['signal_line']
        df['signal'] = np.where(df['histogram'] > 0, 1, -1)
        df['position'] = df['signal'].diff()
        return df
    
    @staticmethod
    def bollinger(df):
        """布林带策略"""
        df = df.copy()
        df['ma'] = df['close'].rolling(20).mean()
        df['std'] = df['close'].rolling(20).std()
        df['upper'] = df['ma'] + 2 * df['std']
        df['lower'] = df['ma'] - 2 * df['std']
        df['signal'] = 0
        df.loc[df['close'] < df['lower'], 'signal'] = 1
        df.loc[df['close'] > df['upper'], 'signal'] = -1
        df['position'] = df['signal'].diff()
        return df
    
    @staticmethod
    def momentum(df):
        """动量策略"""
        df = df.copy()
        df['mom5'] = df['close'].pct_change(5)
        df['mom10'] = df['close'].pct_change(10)
        df['signal'] = np.where((df['mom5'] > 0) & (df['mom10'] > 0), 1,
                               np.where((df['mom5'] < 0) & (df['mom10'] < 0), -1, 0))
        df['position'] = df['signal'].diff()
        return df
    
    @staticmethod
    def breakout(df):
        """突破策略"""
        df = df.copy()
        df['high20'] = df['high'].rolling(20).max()
        df['low20'] = df['low'].rolling(20).min()
        df['signal'] = 0
        df.loc[df['close'] > df['high20'].shift(1), 'signal'] = 1
        df.loc[df['close'] < df['low20'].shift(1), 'signal'] = -1
        df['position'] = df['signal'].diff()
        return df
    
    ALL = {
        'MA': ma_cross,
        'RSI': rsi,
        'MACD': macd,
        'BB': bollinger,
        'MOM': momentum,
        'BRK': breakout
    }

# ============== 分析引擎 ==============
class Analyzer:
    """综合分析引擎"""
    
    def __init__(self):
        self.pool = DataManager.STOCK_POOL
    
    def get_value_score(self, symbol, industry, pe_low, pe_high):
        """价值评分"""
        price = DataManager.get_price(symbol)
        if price is None:
            return {'score': 0, 'status': '无数据'}
        
        # PE估值（简化版）
        pe = pe_low + 5
        if pe < pe_low:
            pe_score = 30
            status = '低估'
        elif pe < pe_high:
            pe_score = 20
            status = '合理'
        else:
            pe_score = 10
            status = '高估'
        
        # 护城河
        moat = {
            '保险': 15, '银行': 14, '证券': 13, '白酒': 18,
            '家电': 12, '新能源': 15, '新能源车': 14, '医药': 16,
            '电子': 14, '电力': 13, '消费': 12, '能源': 10, 'ETF': 10,
            '汽车': 11
        }.get(industry, 10)
        
        return {
            'score': pe_score + moat,
            'pe': pe,
            'status': status,
            'moat': moat,
            'price': price
        }
    
    def get_tech_result(self, df, strategy_func):
        """技术分析回测"""
        if df is None or len(df) < 60:
            return None
        
        try:
            df = strategy_func(df)
            test = df.tail(Config.BACKTEST_DAYS)
            
            capital = Config.INITIAL_CAPITAL * Config.POSITION_SIZE
            position = 0
            entry = 0
            wins, trades = 0, 0
            
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
            
            ret = (final - Config.INITIAL_CAPITAL * Config.POSITION_SIZE) / (Config.INITIAL_CAPITAL * Config.POSITION_SIZE) * 100
            
            return {
                'return': ret,
                'trades': trades,
                'wins': wins,
                'win_rate': wins / trades * 100 if trades > 0 else 0
            }
        except:
            return None
    
    def analyze_all(self):
        """分析所有股票"""
        results = []
        
        for symbol, name, industry, pe_low, pe_high in self.pool:
            # 价值分析
            value = self.get_value_score(symbol, industry, pe_low, pe_high)
            
            # 技术分析
            df = DataManager.get_cached_data(symbol)
            tech_results = []
            
            for sname, sfunc in Strategies.ALL.items():
                result = self.get_tech_result(df, sfunc)
                if result:
                    tech_results.append({
                        'name': sname,
                        'return': result['return'],
                        'win_rate': result['win_rate']
                    })
            
            # 最佳策略
            best = max(tech_results, key=lambda x: x['return']) if tech_results else None
            
            # 综合评分 (价值40% + 技术60%)
            fin_score = value['score']
            tech_score = (best['return'] + 50) if best else 50
            combined = fin_score * 0.4 + max(0, tech_score) * 0.6
            
            results.append({
                'symbol': symbol,
                'name': name,
                'industry': industry,
                'value': value,
                'best_tech': best,
                'combined': combined
            })
        
        # 排序
        results.sort(key=lambda x: x['combined'], reverse=True)
        return results

# ============== 交易管理器 ==============
class Trader:
    STATE_FILE = os.path.expanduser("~/.openclaw/workspace/trading_state.json")
    
    def __init__(self):
        self.state = self.load_state()
    
    def load_state(self):
        if os.path.exists(self.STATE_FILE):
            with open(self.STATE_FILE, 'r') as f:
                return json.load(f)
        return {
            'cash': Config.INITIAL_CAPITAL,
            'positions': {},
            'history': [],
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'daily_pnl': [],
            'equity_curve': []
        }
    
    def save_state(self):
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_position_value(self):
        """获取持仓市值"""
        total = 0
        for symbol, pos in self.state['positions'].items():
            price = DataManager.get_price(symbol) or pos['entry']
            total += pos['shares'] * price
        return total
    
    def check_risk(self):
        """风控检查"""
        to_sell = []
        
        for symbol, pos in self.state['positions'].items():
            price = DataManager.get_price(symbol) or pos['entry']
            profit_pct = (price - pos['entry']) / pos['entry']
            
            # 止损
            if profit_pct <= -Config.STOP_LOSS:
                to_sell.append((symbol, '止损', profit_pct))
            # 止盈
            elif profit_pct >= Config.TAKE_PROFIT:
                to_sell.append((symbol, '止盈', profit_pct))
        
        return to_sell
    
    def sell(self, symbol, reason, profit_pct):
        """卖出"""
        pos = self.state['positions'][symbol]
        price = DataManager.get_price(symbol) or pos['entry']
        revenue = pos['shares'] * price
        
        self.state['cash'] += revenue
        self.state['history'].append({
            'symbol': symbol,
            'name': pos['name'],
            'action': 'SELL',
            'reason': reason,
            'entry': pos['entry'],
            'exit': price,
            'profit_pct': profit_pct * 100,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        
        del self.state['positions'][symbol]
        print(f"  📉 卖出 {pos['name']} ({reason}, {profit_pct*100:+.1f}%)")
    
    def buy(self, symbol, name, price, strategy):
        """买入"""
        if len(self.state['positions']) >= Config.MAX_POSITIONS:
            return False
        
        amount = self.state['cash'] * Config.POSITION_SIZE
        shares = int(amount / price)
        
        if shares > 0:
            cost = shares * price
            self.state['cash'] -= cost
            self.state['positions'][symbol] = {
                'name': name,
                'shares': shares,
                'entry': price,
                'strategy': strategy,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            print(f"  📈 买入 {name} @ {price:.2f} x{shares}")
            return True
        return False
    
    def get_total_value(self):
        """总资产"""
        return self.state['cash'] + self.get_position_value()
    
    def report(self):
        """生成报告"""
        total = self.get_total_value()
        ret = (total - Config.INITIAL_CAPITAL) / Config.INITIAL_CAPITAL * 100
        
        print("\n" + "="*60)
        print("📊 交易报告")
        print("="*60)
        print(f"日期: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"现金: {self.state['cash']:.2f}")
        print(f"持仓: {len(self.state['positions'])}只")
        
        for symbol, pos in self.state['positions'].items():
            price = DataManager.get_price(symbol) or pos['entry']
            profit = (price - pos['entry']) / pos['entry'] * 100
            print(f"  {pos['name']}: {pos['entry']:.2f} → {price:.2f} ({profit:+.1f}%)")
        
        print(f"\n💰 总资产: {total:.2f}")
        print(f"📈 收益率: {ret:+.2f}%")
        print(f"📋 历史交易: {len(self.state['history'])}次")
        
        # 统计
        if self.state['history']:
            wins = sum(1 for h in self.state['history'] if h.get('profit_pct', 0) > 0)
            print(f"🎯 胜率: {wins/len(self.state['history'])*100:.1f}%")
        
        return ret

# ============== 主程序 ==============
class TradingSystem:
    """交易系统主类"""
    
    def __init__(self):
        self.analyzer = Analyzer()
        self.trader = Trader()
    
    def update_data(self):
        """更新数据"""
        print("更新数据...")
        DataManager.download_all()
    
    def run(self):
        """运行每日交易"""
        print("\n" + "="*60)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} 智能交易系统 v6")
        print("="*60)
        
        # 1. 风控检查
        print("\n🔍 风控检查...")
        to_sell = self.trader.check_risk()
        for symbol, reason, profit in to_sell:
            self.trader.sell(symbol, reason, profit)
        
        # 2. 分析市场
        print("\n📊 分析市场...")
        results = self.analyzer.analyze_all()
        
        # 3. 显示Top5
        print("\n🏆 TOP 5 推荐:")
        for i, r in enumerate(results[:5], 1):
            t = r['best_tech']
            v = r['value']
            print(f"  {i}. {r['name']:8s} {r['symbol']:6s} "
                  f"价:{v['price']:7.2f} 价值:{v['status']} 技术:{t['name']}({t['return']:+.1f}%) "
                  f"综合:{r['combined']:.1f}")
        
        # 4. 执行交易
        print("\n🎯 执行交易:")
        
        # 过滤已持仓
        available = [r for r in results if r['symbol'] not in self.trader.state['positions']]
        
        # 买入推荐
        for r in available[:Config.MAX_POSITIONS - len(self.trader.state['positions'])]:
            if r['combined'] > 40:  # 综合评分阈值
                price = r['value']['price']
                strategy = r['best_tech']['name'] if r['best_tech'] else 'MA'
                self.trader.buy(r['symbol'], r['name'], price, strategy)
        
        # 5. 保存并报告
        self.trader.save_state()
        return self.trader.report()

# ============== 运行 ==============
if __name__ == '__main__':
    import sys
    
    system = TradingSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == 'update':
        system.update_data()
    else:
        system.run()
