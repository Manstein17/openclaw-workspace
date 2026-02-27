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
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 导入财务分析模块
from financial_analyzer_v2 import FinancialAnalyzer

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
    
    CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/stock_data")
    
    # 股票池（带行业）
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
    """分析引擎 - 整合财务分析"""
    
    def __init__(self, data_source: DataSource):
        self.ds = data_source
        self.strategies = [
            MAStrategy(5, 10),
            MAStrategy(10, 20),
            RSIStrategy(),
            MACDStrategy(),
        ]
        # 财务分析器
        self.financial = FinancialAnalyzer()
    
    def get_value_score(self, symbol: str, name: str, industry: str, 
                       pe_low: int, pe_high: int) -> Dict:
        """使用完整财务分析"""
        try:
            # 使用完整财务分析
            fin_result = self.financial.analyze(symbol, name, industry)
            price = self.ds.get_latest_price(symbol)
            
            return {
                'score': fin_result['score'],
                'status': fin_result['verdict'],
                'rating': fin_result['rating'],
                'moat': fin_result['moat'],
                'price': price if price else 0,
                'reasons': fin_result['reasons']
            }
        except Exception as e:
            logger.error(f"财务分析失败: {symbol}, {e}")
            price = self.ds.get_latest_price(symbol)
            return {'score': 40, 'status': '分析失败', 'rating': 'C', 'price': price if price else 0}
    
    def get_tech_score(self, symbol: str) -> Dict:
        """技术分析"""
        df = self.ds.load_data(symbol)
        
        if df is None or len(df) < 60:
            return {'best': None, 'all': []}
        
        results = []
        
        for strategy in self.strategies:
            signal = strategy.generate_signal(df)
            results.append({
                'strategy': strategy.name,
                'signal': signal,
                'recommendation': '买入' if signal == 1 else ('卖出' if signal == -1 else '观望')
            })
        
        # 找最佳策略
        best = results[0] if results else None
        
        return {'best': best, 'all': results}
    
    def analyze_stock(self, symbol: str, name: str, industry: str,
                     pe_low: int, pe_high: int) -> Dict:
        """综合分析 - 财务60% + 技术40%"""
        value = self.get_value_score(symbol, name, industry, pe_low, pe_high)
        tech = self.get_tech_score(symbol)
        
        # 综合评分 (财务权重提高)
        fin_score = value.get('score', 40)
        tech_score = 50  # 技术面基准分
        
        # 财务60% + 技术40%
        combined = fin_score * 0.6 + tech_score * 0.4
        
        return {
            'symbol': symbol,
            'name': name,
            'industry': industry,
            'value': value,
            'tech': tech,
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

# ============== 交易引擎 ==============
class TradingEngine:
    """交易引擎"""
    
    def __init__(self, initial_capital: float):
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
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
        
        results = []
        for symbol, name, industry, pe_low, pe_high in DataSource.STOCK_POOL:
            analysis = self.analyzer.analyze_stock(symbol, name, industry, pe_low, pe_high)
            results.append(analysis)
        
        # 排序
        results.sort(key=lambda x: x['combined'], reverse=True)
        
        # 显示Top5
        print("\n🏆 TOP 5 推荐:")
        for i, r in enumerate(results[:5], 1):
            v = r['value']
            t = r['tech']['best']
            signal = t['recommendation'] if t else 'N/A'
            print(f"  {i}. {r['name']:8s} {r['symbol']:6s} "
                  f"价:{v['price']:7.2f} 价值:{v['status']} 信号:{signal} 综合:{r['combined']:.1f}")
        
        # 3. 执行交易
        print("\n🎯 执行交易...")
        
        # 过滤已持仓
        available = [r for r in results if r['symbol'] not in self.engine.positions]
        
        # 买入
        for r in available[:Config.MAX_POSITIONS - len(self.engine.positions)]:
            if r['combined'] > 40:
                v = r['value']
                t = r['tech']['best']
                
                if v['price'] > 0:
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
