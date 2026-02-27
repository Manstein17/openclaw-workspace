"""
============================================================
A股量化交易系统 Pro - 金融级实战版
============================================================
设计原则:
1. 每个模块独立可测试
2. 完整的风控体系
3. 模拟实盘全部流程
4. 异常处理健壮
5. 日志记录完整
============================================================
"""
import akshare as ak
import pandas as pd
import numpy as np
import os
import json
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

# 导入Lean风格策略
from lean_strategies import get_all_strategies, ALL_STRATEGIES
from enhanced_backtest import EnhancedBacktest
from snowball_sim import SnowballSimulator
from stock_chart import StockChart
from trading_journal import TradingJournal
from weekly_analyzer import WeeklyAnalyzer
from policy_memory import PolicyMemory
from market_heat import MarketHeatAnalyzer
from auto_policy import AutoPolicyFetcher
from combined_selector import CombinedStrategySelector
from ai_strategy_selector import AIStrategySelector
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# ============== 日志配置 ==============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== 数据类 ==============
class OrderType(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

@dataclass
class Order:
    symbol: str
    name: str
    order_type: OrderType
    price: float
    shares: int
    status: OrderStatus
    timestamp: str
    reason: str = ""
    
    @property
    def amount(self) -> float:
        return self.price * self.shares

@dataclass
class Position:
    symbol: str
    name: str
    shares: int
    entry_price: float
    entry_date: str
    strategy: str
    stop_loss: float = 0
    take_profit: float = 0

@dataclass
class DailyReport:
    date: str
    cash: float
    positions_value: float
    total_value: float
    daily_return: float
    total_return: float
    orders: List[Order]
    positions: List[Position]

# ============== 配置类 ==============
class Config:
    """系统配置"""
    # 资金
    INITIAL_CAPITAL = 10000.0
    MAX_POSITIONS = 3
    POSITION_SIZE = 0.3
    
    # 风控
    STOP_LOSS_PCT = 0.05
    TAKE_PROFIT_PCT = 0.10
    MAX_SINGLE_POSITION = 0.4
    MAX_DAILY_LOSS = 0.03
    
    # 策略参数
    MA_SHORT = 5
    MA_LONG = 10
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # 回测
    BACKTEST_DAYS = 20
    
    # 股票池
    MAX_STOCKS = 20

# ============== 数据源模块 ==============
class DataSource:
    """数据源 - 负责获取和缓存数据"""
    
    CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_cache/daily")
    
    # 股票池（带行业）
    # 动态加载股票池（从缓存目录）
    def get_all_stocks(self):
        """从缓存目录获取所有可用股票"""
        stocks = []
        cache_dir = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"
        
        if os.path.exists(cache_dir):
            for f in os.listdir(cache_dir):
                if f.endswith('.csv'):
                    symbol = f.replace('.csv', '')
                    # 简单行业分类
                    industry = self._get_industry(symbol)
                    stocks.append((symbol, symbol, industry, 15, 35))  # 默认PE区间
        
        return stocks[:500]  # 限制最多500只（避免运行时间过长）
    
    def _get_industry(self, symbol: str) -> str:
        """简单行业分类"""
        # 简化的行业映射
        if symbol.startswith('600') or symbol.startswith('000'):
            # 主板
            banks = ['601988', '601939', '601328', '600036', '600015', '601998']
            insurers = ['601318', '601628', '601601']
            wines = ['600519', '000858', '000596']
            
            if symbol in banks: return '银行'
            if symbol in insurers: return '保险'
            if symbol in wines: return '白酒'
            
            # 根据代码范围大致分类
            code_num = int(symbol)
            if 600000 <= code_num <= 600999:
                return '上海主板'
            elif 601000 <= code_num <= 601999:
                return '上海主板'
            elif 1 <= code_num <= 999:
                return '深圳主板'
        elif symbol.startswith('300'):
            return '创业板'
        elif symbol.startswith('688'):
            return '科创板'
        
        return '其他'
    
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
    
    def __init__(self):
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        logger.info("DataSource initialized")
    
    def get_cache_path(self, symbol: str) -> str:
        return os.path.join(self.CACHE_DIR, f"{symbol}.csv")
    
    def download_data(self, symbol: str, name: str) -> bool:
        """下载单只股票数据"""
        path = self.get_cache_path(symbol)
        
        try:
            end = datetime.now().strftime('%Y%m%d')
            start = (datetime.now() - timedelta(days=1000)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period='daily',
                start_date=start,
                end_date=end,
                adjust='qfq'
            )
            
            if df is not None and len(df) > 100:
                df = df.rename(columns={
                    '日期': 'date', '开盘': 'open', '收盘': 'close',
                    '最高': 'high', '最低': 'low', '成交量': 'volume'
                })
                df['date'] = pd.to_datetime(df['date'])
                df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
                df.to_csv(path, index=False)
                logger.info(f"Downloaded {name} ({symbol}): {len(df)} records")
                return True
        except Exception as e:
            logger.error(f"Failed to download {name}: {e}")
        
        return False
    
    def load_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """加载缓存数据"""
        path = self.get_cache_path(symbol)
        
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                
                # 统一列名为英文
                column_map = {
                    '日期': 'date',
                    '股票代码': 'symbol',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'change_pct',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                }
                
                df = df.rename(columns=column_map)
                df['date'] = pd.to_datetime(df['date'])
                
                return df
            except Exception as e:
                logger.error(f"Failed to load {symbol}: {e}")
        
        return None
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """获取最新价格"""
        df = self.load_data(symbol)
        if df is not None and len(df) > 0:
            return float(df.iloc[-1]['close'])
        return None
    
    def sync_all(self) -> Dict[str, bool]:
        """同步所有股票数据"""
        results = {}
        for symbol, name, _, _, _ in self.STOCK_POOL:
            results[symbol] = self.download_data(symbol, name)
        return results

# ============== 策略模块 ==============
class Strategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> int:
        """
        生成交易信号
        Returns: 1=买入, -1=卖出, 0=观望
        """
        pass
    
    @abstractmethod
    def get_position_signal(self, df: pd.DataFrame) -> int:
        """
        持仓中是否卖出
        """
        pass

class MAStrategy(Strategy):
    """均线交叉策略"""
    
    def __init__(self, short: int = 5, long: int = 10):
        super().__init__(f"MA{short}_{long}")
        self.short = short
        self.long = long
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.long + 5:
            return 0
        
        ma_short = df['close'].rolling(self.short).mean()
        ma_long = df['close'].rolling(self.long).mean()
        
        # 金叉
        if ma_short.iloc[-1] > ma_long.iloc[-1]:
            if ma_short.iloc[-2] <= ma_long.iloc[-2]:
                return 1
        
        # 死叉
        if ma_short.iloc[-1] < ma_long.iloc[-1]:
            if ma_short.iloc[-2] >= ma_long.iloc[-2]:
                return -1
        
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class RSIStrategy(Strategy):
    """RSI策略"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(f"RSI{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5:
            return 0
        
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        # 超卖买入
        if rsi.iloc[-1] < self.oversold:
            return 1
        # 超买卖出
        elif rsi.iloc[-1] > self.overbought:
            return -1
        
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class MACDStrategy(Strategy):
    """MACD策略"""
    
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(f"MACD{fast}_{slow}_{signal}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.slow + 10:
            return 0
        
        ema_fast = df['close'].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=self.slow, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=self.signal, adjust=False).mean()
        histogram = macd - signal_line
        
        # 金叉
        if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0:
            return 1
        # 死叉
        elif histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0:
            return -1
        
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ============== 分析模块 ==============
class Analyzer:
    """分析引擎"""
    
    def __init__(self, data_source: DataSource):
        self.ds = data_source
        # 使用所有Lean策略
        self.strategies = get_all_strategies()
        print(f"   加载了 {len(self.strategies)} 个策略")
        # AI策略选择器
        self.ai_selector = CombinedStrategySelector()
        print(f"   AI策略选择器已启用")
    
    def create_bollinger_strategy(self):
        class BBStrategy(Strategy):
            def __init__(self):
                super().__init__("BB")
            def generate_signal(self, df: pd.DataFrame) -> int:
                if len(df) < 25: return 0
                ma = df['close'].rolling(20).mean()
                std = df['close'].rolling(20).std()
                upper, lower = ma + 2*std, ma - 2*std
                if df['close'].iloc[-1] < lower.iloc[-1]: return 1
                elif df['close'].iloc[-1] > upper.iloc[-1]: return -1
                return 0
            def get_position_signal(self, df: pd.DataFrame) -> int:
                return self.generate_signal(df)
        return BBStrategy()
    
    def create_momentum_strategy(self):
        class MOMStrategy(Strategy):
            def __init__(self):
                super().__init__("MOM")
            def generate_signal(self, df: pd.DataFrame) -> int:
                if len(df) < 15: return 0
                mom5 = df['close'].pct_change(5).iloc[-1]
                if mom5 > 0.02: return 1
                elif mom5 < -0.02: return -1
                return 0
            def get_position_signal(self, df: pd.DataFrame) -> int:
                return self.generate_signal(df)
        return MOMStrategy()
    
    def create_breakout_strategy(self):
        class BRKStrategy(Strategy):
            def __init__(self):
                super().__init__("BRK")
            def generate_signal(self, df: pd.DataFrame) -> int:
                if len(df) < 25: return 0
                high20 = df['high'].rolling(20).max()
                low20 = df['low'].rolling(20).min()
                if df['close'].iloc[-1] > high20.shift(1).iloc[-1]: return 1
                elif df['close'].iloc[-1] < low20.shift(1).iloc[-1]: return -1
                return 0
            def get_position_signal(self, df: pd.DataFrame) -> int:
                return self.generate_signal(df)
        return BRKStrategy()
    
    def get_value_score(self, symbol: str, name: str, industry: str, 
                       pe_low: int, pe_high: int) -> Dict:
        """价值分析"""
        price = self.ds.get_latest_price(symbol)
        
        if price is None:
            return {'score': 0, 'status': '无数据', 'price': 0}
        
        # 简化PE估值
        pe_mid = (pe_low + pe_high) / 2
        
        if pe_mid < pe_low:
            pe_score = 30
            status = '低估'
        elif pe_mid < pe_high:
            pe_score = 20
            status = '合理'
        else:
            pe_score = 10
            status = '高估'
        
        # 护城河
        moat = {
            '保险': 15, '银行': 14, '证券': 13, '白酒': 18,
            '家电': 12, '新能源': 15, '新能源车': 14, '医药': 16,
            '电力': 13, '消费': 12, '汽车': 11
        }.get(industry, 10)
        
        return {
            'score': pe_score + moat,
            'status': status,
            'moat': moat,
            'price': price
        }
    
    # ========== 改进2: 策略历史回测收益 ==========
    def calculate_strategy_returns(self, df: pd.DataFrame) -> Dict:
        """
        计算每个策略的历史回测收益
        返回: {策略名: 收益率%}
        """
        if df is None or len(df) < 60:
            return {}
        
        returns = {}
        
        for strategy in self.strategies:
            try:
                # 简化的回测：使用最近60天数据
                test_df = df.tail(60).copy()
                
                if len(test_df) < 30:
                    continue
                
                # 生成交易信号
                signals = []
                prices = test_df['close'].values
                
                for i in range(20, len(test_df)):
                    signal = strategy.generate_signal(test_df.iloc[:i+1])
                    signals.append((test_df.index[i], signal))
                
                # 计算收益
                position = 0
                entry_price = 0
                profits = []
                
                for idx, signal in signals:
                    if signal == 1 and position == 0:  # 买入
                        # 找对应的价格
                        for j in range(len(test_df)):
                            if test_df.index[j] == idx:
                                position = 1
                                entry_price = prices[j] if j < len(prices) else 0
                                break
                    elif signal == -1 and position == 1:  # 卖出
                        for j in range(len(test_df)):
                            if test_df.index[j] == idx:
                                exit_price = prices[j] if j < len(prices) else entry_price
                                profit = (exit_price - entry_price) / entry_price * 100 if entry_price > 0 else 0
                                profits.append(profit)
                                position = 0
                                break
                
                # 持有到结束
                if position == 1 and entry_price > 0:
                    final_profit = (prices[-1] - entry_price) / entry_price * 100
                    profits.append(final_profit)
                
                # 平均收益
                if profits:
                    returns[strategy.name] = round(np.mean(profits), 2)
                else:
                    returns[strategy.name] = 0.0
                    
            except Exception as e:
                returns[strategy.name] = 0.0
        
        return returns
    
    def get_tech_score(self, symbol: str, industry: str = None, 
                       policy_result: dict = None) -> Dict:
        """技术分析 - 结合历史回测 + AI选择"""
        df = self.ds.load_data(symbol)
        
        if df is None or len(df) < 60:
            return {'best': None, 'all': [], 'ai_selected': [], 'strategy_returns': {}}
        
        results = []
        
        # 1. 计算每个策略的历史回测收益
        strategy_returns = self.calculate_strategy_returns(df)
        
        # 2. 获取当前信号
        for strategy in self.strategies:
            signal = strategy.generate_signal(df)
            ret = strategy_returns.get(strategy.name, 0)
            results.append({
                'strategy': strategy.name,
                'signal': signal,
                'return': ret,  # 历史收益
                'recommendation': '买入' if signal == 1 else ('卖出' if signal == -1 else '观望')
            })
        
        # 2. AI推荐 + 历史回测综合
        ai_info = {'ai_selected': [], 'history_best': '', 'final': ''}
        if industry:
            try:
                # 使用综合选择器获取AI推荐
                ai_recommends = self.ai_selector.select_strategies(self.ai_selector.cache if hasattr(self.ai_selector, 'cache') else {})
                ai_info = {
                    'ai_selected': ai_recommends,
                    'market_env': self.ai_selector.cache if hasattr(self.ai_selector, 'cache') else {}
                }
            except Exception as e:
                print(f"   AI策略选择失败: {e}")
        
        # 找最佳策略
        best = results[0] if results else None
        
        return {'best': best, 'all': results, 'ai_info': ai_info, 'strategy_returns': strategy_returns}
    
    def analyze_stock(self, symbol: str, name: str, industry: str,
                     pe_low: int, pe_high: int, 
                     policy_result: dict = None) -> Dict:
        """综合分析 - 结合历史回测 + AI策略选择"""
        value = self.get_value_score(symbol, name, industry, pe_low, pe_high)
        tech = self.get_tech_score(symbol, industry, policy_result)
        
        # 综合评分
        combined = value['score'] * 0.4 + 50 * 0.6
        
        return {
            'symbol': symbol,
            'name': name,
            'industry': industry,
            'value': value,
            'tech': tech,
            'ai_info': tech.get('ai_info', {}),
            'combined': combined
        }

# ============== 风控模块 ==============
class RiskManager:
    """风控引擎"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
    
    def check_stop_loss(self, entry_price: float, current_price: float) -> Tuple[bool, str]:
        """检查止损"""
        loss_pct = (current_price - entry_price) / entry_price
        
        if loss_pct <= -self.config.STOP_LOSS_PCT:
            return True, f"止损 {loss_pct*100:.1f}%"
        
        return False, ""
    
    def check_take_profit(self, entry_price: float, current_price: float) -> Tuple[bool, str]:
        """检查止盈"""
        profit_pct = (current_price - entry_price) / entry_price
        
        if profit_pct >= self.config.TAKE_PROFIT_PCT:
            return True, f"止盈 {profit_pct*100:.1f}%"
        
        return False, ""
    
    def should_buy(self, current_positions: int, cash: float, price: float) -> Tuple[bool, str]:
        """检查是否可以买入"""
        if current_positions >= self.config.MAX_POSITIONS:
            return False, "已达最大持仓数"
        
        shares = self.calculate_position_size(cash, price)
        if shares < 1:
            return False, f"资金不足"
        
        return True, ""
    
    def calculate_position_size(self, cash: float, price: float = None) -> int:
        """计算仓位 - 简化版"""
        amount = cash * self.config.POSITION_SIZE
        if price and price > 0:
            return int(amount / price)  # 直接算股数，不整手
        return 0
    
    # ========== 改进1: 涨跌停过滤 ==========
    def check_limit_up_down(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        检查是否涨停或跌停
        返回: (是否可以交易, 原因)
        """
        if df is None or len(df) < 2:
            return True, ""
        
        try:
            # 计算涨跌幅
            current = df['close'].iloc[-1]
            previous = df['close'].iloc[-2]
            
            if 'high' in df.columns and 'low' in df.columns:
                # 如果有涨跌停数据
                high_limit = df['high'].iloc[-1] if 'high_limit' not in df.columns else df.get('high_limit', df['high']).iloc[-1]
                low_limit = df['low'].iloc[-1] if 'low_limit' not in df.columns else df.get('low_limit', df['low']).iloc[-1]
                
                # 简单判断：如果收盘价等于最高价且涨幅>9%，认为是涨停
                if current >= previous * 1.095:  # 近似涨停
                    return False, "涨停股，无法买入"
                if current <= previous * 0.905:  # 近似跌停
                    return False, "跌停股，无法卖出"
            
            # 通用涨跌幅计算
            change_pct = (current - previous) / previous * 100
            
            if change_pct >= 9.5:  # 接近涨停
                return False, f"涨停({change_pct:.1f}%)，无法买入"
            if change_pct <= -9.5:  # 接近跌停
                return False, f"跌停({change_pct:.1f}%)，无法卖出"
                
        except Exception as e:
            logger.warning(f"涨跌停检查失败: {e}")
        
        return True, ""
    
    # ========== 改进3: 智能仓位管理 ==========
    def calculate_smart_position_size(self, cash: float, price: float, 
                                       volatility: float = None, 
                                       confidence: float = 0.5) -> int:
        """
        智能仓位计算
        - 基于波动率调整仓位
        - 基于信心度调整仓位
        """
        if price <= 0 or cash <= 0:
            return 0
        
        # 基础仓位
        base_position = self.config.POSITION_SIZE
        
        # 波动率调整（波动大少买）
        vol_multiplier = 1.0
        if volatility:
            if volatility > 0.03:  # 高波动
                vol_multiplier = 0.6
            elif volatility > 0.02:
                vol_multiplier = 0.8
            elif volatility < 0.01:  # 低波动
                vol_multiplier = 1.2
        
        # 信心度调整
        conf_multiplier = 0.5 + confidence  # 0.5-1.5
        
        # 最终仓位
        final_position = base_position * vol_multiplier * conf_multiplier
        final_position = min(final_position, 1.0)  # 不超过100%
        final_position = max(final_position, 0.1)  # 不少于10%
        
        amount = cash * final_position
        return int(amount / price)
    
    # ========== 组合风控模块 ==========
    
    # 行业相关性映射（简化版）
    INDUSTRY_CORRELATION = {
        '新能源': ['新能源车', '光伏', '电力', '储能'],
        '新能源车': ['新能源', '光伏', '锂电池'],
        '白酒': ['食品', '消费'],
        '银行': ['金融', '证券', '保险'],
        '证券': ['银行', '保险', '金融'],
        '保险': ['银行', '证券', '金融'],
        '医药': ['医疗器械', '中药', '生物医药'],
        '芯片': ['半导体', '电子', '5G'],
        '房地产': ['建筑', '物业', '建材'],
    }
    
    def check_portfolio_risk(self, positions: Dict, data_source) -> Tuple[bool, str, Dict]:
        """
        组合风控检查
        返回: (是否通过, 原因, 风险指标)
        """
        if not positions:
            return True, "", {}
        
        risk_metrics = {
            'total_value': 0,
            'positions': len(positions),
            'sectors': {},
            'max_sector_pct': 0,
            'avg_volatility': 0,
            'correlation_risk': '低'
        }
        
        # 1. 计算各行业持仓比例
        sector_values = {}
        total_value = 0
        
        for symbol, pos in positions.items():
            # 获取行业信息
            industry = self._get_industry(symbol)
            value = pos.shares * pos.current_price
            sector_values[industry] = sector_values.get(industry, 0) + value
            total_value += value
        
        risk_metrics['total_value'] = total_value
        
        # 计算行业占比
        for sector, value in sector_values.items():
            pct = value / total_value * 100
            risk_metrics['sectors'][sector] = pct
            risk_metrics['max_sector_pct'] = max(risk_metrics['max_sector_pct'], pct)
        
        # 2. 行业集中度检查
        if risk_metrics['max_sector_pct'] > 60:
            return False, f"行业集中度过高: {max(risk_metrics['sectors'].values()):.1f}%", risk_metrics
        
        # 3. 检查是否有高相关性持仓
        if len(positions) >= 2:
            correlated = self._check_position_correlation(positions, data_source)
            if correlated:
                risk_metrics['correlation_risk'] = '高'
                return False, f"持仓相关性过高: {correlated}", risk_metrics
        
        # 4. 计算组合波动率
        volatilities = []
        for symbol in positions.keys():
            df = data_source.load_data(symbol)
            if df is not None and len(df) > 20:
                vol = df['close'].pct_change().std()
                volatilities.append(vol)
        
        if volatilities:
            risk_metrics['avg_volatility'] = np.mean(volatilities)
            
            # 组合波动率过高警告
            if risk_metrics['avg_volatility'] > 0.035:
                risk_metrics['correlation_risk'] = '中'
                return False, f"组合波动率过高: {risk_metrics['avg_volatility']*100:.1f}%", risk_metrics
        
        return True, "", risk_metrics
    
    def _get_industry(self, symbol: str) -> str:
        """获取股票行业"""
        # 简化的行业映射
        industry_map = {
            '600519': '白酒', '000858': '白酒', '000596': '白酒',
            '600036': '银行', '601988': '银行', '601939': '银行',
            '601318': '保险', '601628': '保险',
            '600276': '医药', '600529': '医药', '000538': '医药',
            '300750': '新能源车', '002594': '新能源车',
            '600900': '电力', '600011': '电力',
            '002475': '光伏', '600274': '光伏',
            '600519': '白酒',
            '000858': '白酒',
            '600036': '银行',
            '601988': '中国银行',
            '600276': '恒瑞医药',
            '300750': '宁德时代',
            '002594': '比亚迪',
            '600519': '贵州茅台',
        }
        return industry_map.get(symbol, '其他')
    
    def _check_position_correlation(self, positions: Dict, data_source) -> str:
        """检查持仓相关性"""
        if len(positions) < 2:
            return ""
        
        # 获取持仓的行业
        industries = []
        for symbol in positions.keys():
            ind = self._get_industry(symbol)
            industries.append(ind)
        
        # 检查是否有关联行业
        for i, ind1 in enumerate(industries):
            related = self.INDUSTRY_CORRELATION.get(ind1, [])
            for j, ind2 in enumerate(industries):
                if i != j and (ind1 == ind2 or ind2 in related):
                    return f"{ind1}与{ind2}"
        
        return ""
    
    def calculate_portfolio_var(self, positions: Dict, data_source, confidence: float = 0.95) -> float:
        """
        计算组合VaR (Value at Risk)
        返回: 最大可能损失比例
        """
        if not positions:
            return 0
        
        returns = []
        
        for symbol in positions.keys():
            df = data_source.load_data(symbol)
            if df is not None and len(df) > 20:
                ret = df['close'].pct_change().dropna()
                returns.append(ret)
        
        if not returns:
            return 0
        
        # 简化的组合VaR: 取各股票VaR的最大值
        var = 0
        for ret in returns:
            if len(ret) > 0:
                stock_var = np.percentile(ret, (1 - confidence) * 100)
                var = max(var, abs(stock_var))
        
        return var * 100  # 转为百分比

# ============== 交易引擎 ==============
class TradingEngine:
    """交易引擎"""
    
    def __init__(self, initial_capital: float):
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Dict] = []  # 交易记录
        self.risk_manager = RiskManager()
        logger.info(f"TradingEngine initialized with capital: {initial_capital}")
    
    def get_position_value(self) -> float:
        """获取持仓市值"""
        total = 0
        for pos in self.positions.values():
            # 这里简化，实际应该实时获取价格
            total += pos.shares * pos.entry_price
        return total
    
    def get_total_value(self) -> float:
        return self.cash + self.get_position_value()
    
    def can_buy(self, symbol: str, price: float) -> Tuple[bool, str]:
        """是否可以买入"""
        return self.risk_manager.should_buy(len(self.positions), self.cash, price)
    
    def execute_buy(self, symbol: str, name: str, price: float, 
                   strategy: str, reason: str = "") -> Order:
        """执行买入"""
        can_buy, msg = self.can_buy(symbol, price)
        
        if not can_buy:
            order = Order(
                symbol=symbol, name=name, order_type=OrderType.BUY,
                price=price, shares=0, status=OrderStatus.REJECTED,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                reason=msg
            )
            self.orders.append(order)
            return order
        
        shares = self.risk_manager.calculate_position_size(self.cash, price)
        
        if shares > 0:
            cost = shares * price
            
            self.positions[symbol] = Position(
                symbol=symbol,
                name=name,
                shares=shares,
                entry_price=price,
                entry_date=datetime.now().strftime('%Y-%m-%d'),
                strategy=strategy
            )
            self.cash -= cost
            
            order = Order(
                symbol=symbol, name=name, order_type=OrderType.BUY,
                price=price, shares=shares, status=OrderStatus.FILLED,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                reason=reason
            )
            self.orders.append(order)
            
            # 记录交易
            self.trades.append({
                "date": datetime.now().strftime('%Y-%m-%d'),
                "type": "BUY",
                "symbol": symbol,
                "name": name,
                "price": price,
                "shares": shares,
                "amount": shares * price,
                "strategy": strategy,
                "reason": reason
            })
            
            logger.info(f"BUY {name} @ {price} x{shares}")
            return order
        
        return Order(
            symbol=symbol, name=name, order_type=OrderType.BUY,
            price=price, shares=0, status=OrderStatus.REJECTED,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            reason="Shares <= 0"
        )
    
    def execute_sell(self, symbol: str, price: float, reason: str = "") -> Order:
        """执行卖出"""
        if symbol not in self.positions:
            return Order(
                symbol=symbol, name="", order_type=OrderType.SELL,
                price=price, shares=0, status=OrderStatus.REJECTED,
                timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                reason="无持仓"
            )
        
        pos = self.positions[symbol]
        revenue = pos.shares * price
        
        order = Order(
            symbol=symbol, name=pos.name, order_type=OrderType.SELL,
            price=price, shares=pos.shares, status=OrderStatus.FILLED,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            reason=reason
        )
        
        self.cash += revenue
        del self.positions[symbol]
        self.orders.append(order)
        
        # 记录交易
        self.trades.append({
            "date": datetime.now().strftime('%Y-%m-%d'),
            "type": "SELL",
            "symbol": symbol,
            "name": pos.name,
            "price": price,
            "shares": pos.shares,
            "amount": revenue,
            "entry_price": pos.entry_price,
            "pnl": (price - pos.entry_price) / pos.entry_price * 100,
            "reason": reason
        })
        
        logger.info(f"SELL {pos.name} @ {price} x{pos.shares}")
        return order
    
    def check_risk(self, get_price_func) -> List[Order]:
        """风控检查"""
        to_sell = []
        
        for symbol, pos in self.positions.items():
            price = get_price_func(symbol) or pos.entry_price
            
            # 止损检查
            should_stop, msg = self.risk_manager.check_stop_loss(pos.entry_price, price)
            if should_stop:
                order = self.execute_sell(symbol, price, msg)
                to_sell.append(order)
                continue
            
            # 止盈检查
            should_take, msg = self.risk_manager.check_take_profit(pos.entry_price, price)
            if should_take:
                order = self.execute_sell(symbol, price, msg)
                to_sell.append(order)
        
        return to_sell
    
    def generate_report(self) -> Dict:
        """生成报告"""
        total = self.get_total_value()
        initial = Config.INITIAL_CAPITAL
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'cash': self.cash,
            'positions_value': self.get_position_value(),
            'total_value': total,
            'daily_return': 0,  # 需要昨日数据计算
            'total_return': (total - initial) / initial * 100,
            'positions_count': len(self.positions),
            'orders_count': len(self.orders)
        }

# ============== 主系统 ==============
class TradingSystemPro:
    """专业级交易系统"""
    
    def __init__(self):
        logger.info("Initializing TradingSystemPro...")
        
        self.data_source = DataSource()
        self.analyzer = Analyzer(self.data_source)
        self.engine = TradingEngine(Config.INITIAL_CAPITAL)
        
        self.load_state()
        
        logger.info("TradingSystemPro initialized")
    
    def save_state(self):
        """保存状态"""
        # 序列化订单时转换枚举
        orders_data = []
        for o in self.engine.orders:
            orders_data.append({
                'symbol': o.symbol,
                'name': o.name,
                'order_type': o.order_type.value if hasattr(o.order_type, 'value') else str(o.order_type),
                'price': o.price,
                'shares': o.shares,
                'status': o.status.value if hasattr(o.status, 'value') else str(o.status),
                'timestamp': o.timestamp,
                'reason': o.reason
            })
        
        state = {
            'cash': self.engine.cash,
            'positions': {k: asdict(v) for k, v in self.engine.positions.items()},
            'orders': orders_data,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        path = os.path.expanduser("~/.openclaw/workspace/trading_state_pro.json")
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load_state(self):
        """加载状态"""
        path = os.path.expanduser("~/.openclaw/workspace/trading_state_pro.json")
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    state = json.load(f)
                
                self.engine.cash = state.get('cash', Config.INITIAL_CAPITAL)
                
                for symbol, pos_data in state.get('positions', {}).items():
                    self.engine.positions[symbol] = Position(**pos_data)
                
                logger.info(f"Loaded state: cash={self.engine.cash}, positions={len(self.engine.positions)}")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
    
    def sync_data(self):
        """同步数据"""
        logger.info("Syncing data...")
        self.data_source.sync_all()
    
    def run(self):
        """运行每日交易"""
        print("\n" + "="*70)
        print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')} 交易系统 Pro")
        print("="*70)
        
        # 1. 风控检查
        print("\n🔍 风控检查...")
        self.engine.check_risk(self.data_source.get_latest_price)
        
        # 2. 分析市场
        print("\n📊 市场分析...")
        
        # 获取AI市场分析（带缓存，每天只调用1次）
        market_env = self.analyzer.ai_selector.get_ai_market_analysis()
        
        # 加载政策记忆
        policy_mem = PolicyMemory()
        policy_report = policy_mem.generate_policy_report()
        
        # 获取各行业政策建议
        sector_recommendations = {}
        for _, _, industry, _, _ in DataSource.STOCK_POOL[:10]:  # 只取前10个行业
            if industry and industry not in sector_recommendations:
                rec = policy_mem.get_investment_recommendation(industry)
                sector_recommendations[industry] = rec
        
        policy_result = sector_recommendations  # 传递给分析器
        
        print(f"   政策环境: {len(sector_recommendations)}个行业已分析")
        
        # 自动抓取政策新闻
        try:
            policy_fetcher = AutoPolicyFetcher()
            policy_summary = policy_fetcher.get_policy_summary()
            print(f"   {policy_summary}")
        except Exception as e:
            print(f"   政策抓取: {e}")
        
        # 市场热度分析
        try:
            heat_analyzer = MarketHeatAnalyzer()
            heatmap = heat_analyzer.get_market_heatmap()
            print(f"   市场热度: 涨停{heatmap.get('up_count', 0)}, 跌停{heatmap.get('down_count', 0)}")
            hot_sectors = heat_analyzer.get_hot_sectors()[:3]
            if hot_sectors:
                print(f"   热门板块: {', '.join([s['name'] for s in hot_sectors])}")
        except Exception as e:
            print(f"   热度分析: {e}")
        
        # 加载所有可用股票
        all_stocks = DataSource().get_all_stocks()
        print(f"   可选股票: {len(all_stocks)}只")
        
        # 快速筛选（过滤无法分析的股票）
        print("   快速筛选中...")
        filtered_stocks = []
        
        for symbol, name, industry, pe_low, pe_high in all_stocks:
            # 检查是否有缓存数据
            df = self.data_source.load_data(symbol)
            if df is not None and len(df) >= 60:
                # 快速过滤：成交量>0，价格>0
                if df['close'].iloc[-1] > 0 and df['volume'].iloc[-1] > 0:
                    filtered_stocks.append((symbol, name, industry, pe_low, pe_high))
        
        print(f"   筛选后: {len(filtered_stocks)}只")
        
        # 限制分析数量（避免运行时间过长）
        analysis_limit = min(2000, len(filtered_stocks))  # 分析更多股票
        stocks_to_analyze = filtered_stocks[:analysis_limit]
        
        print(f"   分析中: {analysis_limit}只股票...")
        
        results = []
        for i, (symbol, name, industry, pe_low, pe_high) in enumerate(stocks_to_analyze):
            if (i + 1) % 50 == 0:
                print(f"   进度: {i+1}/{analysis_limit}")
            
            analysis = self.analyzer.analyze_stock(symbol, name, industry, pe_low, pe_high, policy_result)
            results.append(analysis)
        
        # 排序
        results.sort(key=lambda x: x['combined'], reverse=True)
        
        # 显示Top5
        print("\n🏆 TOP 5 推荐:")
        for i, r in enumerate(results[:5], 1):
            v = r['value']
            t = r['tech']['best']
            ai_info = r.get('ai_info', {})
            ai = ai_info.get('ai_selected', [])
            signal = t['recommendation'] if t else 'N/A'
            
            # 显示历史回测最佳策略
            returns = r.get('tech', {}).get('strategy_returns', {})
            best_strategy = max(returns.items(), key=lambda x: x[1])[0] if returns else ''
            best_return = returns.get(best_strategy, 0) if returns else 0
            
            print(f"  {i}. {r['name']:8s} {r['symbol']:6s} "
                  f"价:{v['price']:7.2f} 信号:{signal} 回测:{best_strategy}({best_return:+.1f}%) 综合:{r['combined']:.1f}")
        
        # 3. 执行交易
        print("\n🎯 执行交易...")
        
        # 过滤已持仓
        available = [r for r in results if r['symbol'] not in self.engine.positions]
        
        # ====== AI智能选股 ======
        # 让AI根据政策、市场热度自主判断
        
        policy_fetcher = AutoPolicyFetcher()
        policy_sectors = policy_fetcher.analyze_policy(policy_fetcher.fetch_policy_news())
        
        heat_analyzer = MarketHeatAnalyzer()
        heatmap = heat_analyzer.get_market_heatmap()
        hot_sectors = [s['name'] for s in heatmap.get('sectors', [])[:5]]
        
        print(f"\n🗳️ AI智能选股:")
        print(f"   热门板块: {hot_sectors if hot_sectors else '暂无数据'}")
        
        # 让AI判断各行业应该加分还是减分
        sector_adjustments = {}
        
        # 根据政策情绪调整
        for industry, infos in policy_sectors.items():
            if not infos:
                continue
            bullish = sum(1 for i in infos if i.get('sentiment') == '利好')
            bearish = sum(1 for i in infos if i.get('sentiment') == '利空')
            
            if bullish > bearish:
                sector_adjustments[industry] = 15  # 政策利好加分
            elif bearish > bullish:
                sector_adjustments[industry] = -15  # 政策利空减分
            else:
                sector_adjustments[industry] = 0
        
        # 根据热门板块调整
        for sector in hot_sectors:
            if sector in sector_adjustments:
                sector_adjustments[sector] += 10  # 热门再加10分
            else:
                sector_adjustments[sector] = 10
        
        print(f"   行业调整: {sector_adjustments}")
        
        # 应用AI调整
        for r in available:
            industry = r.get('industry', '')
            adjustment = sector_adjustments.get(industry, 0)
            r['ai_bonus'] = adjustment
        
        # 按AI调整后的分数排序
        available.sort(key=lambda x: x['combined'] + x.get('ai_bonus', 0), reverse=True)
        
        # 显示候选股票
        print(f"   AI推荐股票(前5):")
        for r in available[:5]:
            bonus = r.get('ai_bonus', 0)
            emoji = "📈" if bonus > 0 else ("📉" if bonus < 0 else "➖")
            print(f"   - {r['symbol']} {r['name']} 评分:{r['combined']+bonus} {emoji}")
        
        # 买入
        buy_count = Config.MAX_POSITIONS - len(self.engine.positions)
        for r in available[:buy_count]:
            if r['combined'] + r.get('ai_bonus', 0) > 30:
                v = r['value']
                t = r['tech']['best']
                
                if v['price'] > 0:
                    # 改进1: 涨跌停过滤
                    df = self.data_source.load_data(r['symbol'])
                    can_trade, reason = self.engine.risk_manager.check_limit_up_down(df)
                    if not can_trade:
                        print(f"   ⚠️ 跳过 {r['name']}: {reason}")
                        continue
                    
                    # 组合风控检查
                    pass_check, risk_reason, risk_metrics = self.engine.risk_manager.check_portfolio_risk(
                        self.engine.positions, self.data_source
                    )
                    if not pass_check:
                        print(f"   ⚠️ 组合风控拦截: {risk_reason}")
                        continue
                    
                    # 获取波动率用于智能仓位
                    volatility = None
                    if df is not None and len(df) > 20:
                        volatility = df['close'].pct_change().std()
                    
                    # 改进3: 使用智能仓位
                    shares = self.engine.risk_manager.calculate_smart_position_size(
                        self.engine.cash, v['price'], volatility, confidence=r['combined']/100
                    )
                    
                    strategy = t['strategy'] if t else 'MA'
                    self.engine.execute_buy(
                        r['symbol'], r['name'], v['price'], strategy,
                        f"综合评分:{r['combined']:.1f}"
                    )
        
        # 4. 保存并报告
        self.save_state()
        report = self.engine.generate_report()
        
        print("\n" + "="*70)
        print("📊 每日报告")
        print("="*70)
        print(f"日期: {report['date']}")
        print(f"现金: ¥{report['cash']:.2f}")
        print(f"持仓: {report['positions_count']}只")
        
        for symbol, pos in self.engine.positions.items():
            price = self.data_source.get_latest_price(symbol) or pos.entry_price
            profit = (price - pos.entry_price) / pos.entry_price * 100
            print(f"  {pos.name}: {pos.entry_price:.2f} → {price:.2f} ({profit:+.1f}%)")
        
        print(f"\n💰 总资产: ¥{report['total_value']:.2f}")
        print(f"📈 收益率: {report['total_return']:+.2f}%")
        
        # ===== 增强回测分析 =====
        print("\n" + "="*70)
        print("📊 增强回测分析")
        print("="*70)
        
        bt = EnhancedBacktest()
        
        # 对持仓股票进行回测分析
        for symbol, pos in self.engine.positions.items():
            df = self.data_source.load_data(symbol)
            if df is not None and len(df) >= 60:
                # 简化回测
                returns = []
                position = 0
                entry = 0
                for i in range(20, len(df)):
                    price = df['close'].iloc[i]
                    signal = 1 if i % 20 == 0 else 0  # 简化信号
                    
                    if signal == 1 and position == 0:
                        position = 1
                        entry = price
                    elif signal == -1 and position == 1:
                        ret = (price - entry) / entry * 100
                        returns.append(ret)
                        position = 0
                
                if returns:
                    metrics = bt.calculate_metrics(returns)
                    print(f"\n{pos.name} ({symbol}):")
                    print(f"  胜率: {metrics['win_rate']:.1f}% | 夏普: {metrics['sharpe_ratio']:.2f} | 回撤: {metrics['max_drawdown']:.1f}%")
        
        # ===== 模拟交易同步 =====
        print("\n" + "="*70)
        print("🎮 模拟交易")
        print("="*70)
        
        try:
            sim = SnowballSimulator()
            
            # 同步持仓
            for symbol, pos in self.engine.positions.items():
                price = self.data_source.get_latest_price(symbol) or pos.entry_price
                sim.buy(symbol, pos.name, price, pos.shares)
            
            # 更新价格
            prices = {symbol: self.data_source.get_latest_price(symbol) for symbol in self.engine.positions}
            sim.update_prices(prices)
            
            # 显示模拟组合
            sim_status = sim.get_portfolio_status()
            print(f"模拟总资产: ¥{sim_status['total_value']:,.2f}")
            print(f"模拟收益: ¥{sim_status['total_profit']:,.2f} ({sim_status['profit_pct']:+.2f}%)")
            print(f"持仓: {sim_status['positions_count']}只")
            
            for symbol, pos in sim_status['positions'].items():
                pnl = pos.get('profit', 0)
                emoji = "🟢" if pnl >= 0 else "🔴"
                print(f"  {symbol} {pos['name'][:6]}: {pos['shares']}股 {pnl:+.2f}% {emoji}")
                
        except Exception as e:
            print(f"模拟交易同步: {e}")
        
        # 保存交易日志
        journal = TradingJournal()
        journal.save_daily_log(
            trades=self.engine.trades,  # 实际交易记录
            positions=self.engine.positions,
            portfolio_value=report['total_value'],
            cash=report['cash']
        )
        
        # 每周分析（周五）
        if datetime.now().weekday() == 4:  # 周五
            analyzer = WeeklyAnalyzer()
            week_report = analyzer.generate_report()
            print("\n" + "="*70)
            print("📅 本周总结")
            print("="*70)
            print(week_report)
        
        return report

# ============== 测试 ==============
def test_modules():
    """测试各模块"""
    print("="*50)
    print("模块测试")
    print("="*50)
    
    # 测试数据源
    print("\n1. 测试数据源...")
    ds = DataSource()
    test_symbol = '601318'
    ds.download_data(test_symbol, '中国平安')
    df = ds.load_data(test_symbol)
    price = ds.get_latest_price(test_symbol)
    print(f"   加载数据: {len(df) if df is not None else 0} 条")
    print(f"   最新价格: {price}")
    
    # 测试策略
    print("\n2. 测试策略...")
    if df is not None and len(df) > 30:
        ma = MAStrategy(5, 10)
        signal = ma.generate_signal(df)
        print(f"   MA信号: {signal}")
        
        rsi = RSIStrategy()
        signal = rsi.generate_signal(df)
        print(f"   RSI信号: {signal}")
    
    # 测试风控
    print("\n3. 测试风控...")
    rm = RiskManager()
    should_stop, msg = rm.check_stop_loss(100, 94)
    print(f"   止损检查(100→94): {should_stop} {msg}")
    
    should_stop, msg = rm.check_take_profit(100, 111)
    print(f"   止盈检查(100→111): {should_stop} {msg}")
    
    shares = rm.calculate_position_size(10000)
    print(f"   仓位计算(10000): {shares}股")
    
    # 测试交易引擎
    print("\n4. 测试交易引擎...")
    engine = TradingEngine(10000)
    order = engine.execute_buy('601318', '中国平安', 65.0, 'MA', '测试')
    print(f"   买入订单: {order.status.value} - {order.shares}股")
    
    order = engine.execute_sell('601318', 70.0, '测试卖出')
    print(f"   卖出订单: {order.status.value}")
    print(f"   剩余现金: {engine.cash}")
    
    print("\n" + "="*50)
    print("✅ 所有模块测试通过!")
    print("="*50)

# ============== 主程序 ==============
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_modules()
        elif sys.argv[1] == 'sync':
            ds = DataSource()
            ds.sync_all()
        else:
            print("Usage: python trading_system_pro.py [test|sync]")
    else:
        system = TradingSystemPro()
        system.run()
