"""
完整的策略模块 - Lean风格
包含所有常用量化交易策略
"""
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class Strategy(ABC):
    """策略基类"""
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> int:
        """生成信号: 1=买入, -1=卖出, 0=观望"""
        pass
    
    @abstractmethod
    def get_position_signal(self, df: pd.DataFrame) -> int:
        """持仓中信号"""
        pass

# ==================== 趋势策略 ====================

class MAIntersection(Strategy):
    """均线交叉策略 (MovingAverageCross)"""
    def __init__(self, short: int = 5, long: int = 10):
        super().__init__(f"MA{short}_{long}")
        self.short = short
        self.long = long
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.long + 5: return 0
        ma_s = df['close'].rolling(self.short).mean()
        ma_l = df['close'].rolling(self.long).mean()
        
        if ma_s.iloc[-1] > ma_l.iloc[-1] and ma_s.iloc[-2] <= ma_l.iloc[-2]: return 1
        if ma_s.iloc[-1] < ma_l.iloc[-1] and ma_s.iloc[-2] >= ma_l.iloc[-2]: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class MACDTrend(Strategy):
    """MACD趋势策略"""
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(f"MACD{fast}_{slow}_{signal}")
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.slow + 10: return 0
        ema_f = df['close'].ewm(span=self.fast, adjust=False).mean()
        ema_s = df['close'].ewm(span=self.slow, adjust=False).mean()
        macd = ema_f - ema_s
        sig = macd.ewm(span=self.signal, adjust=False).mean()
        hist = macd - sig
        
        if hist.iloc[-1] > 0 and hist.iloc[-2] <= 0: return 1
        if hist.iloc[-1] < 0 and hist.iloc[-2] >= 0: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class ParabolicSAR(Strategy):
    """抛物线转向策略"""
    def __init__(self, af_start: float = 0.02, af_increment: float = 0.02, af_max: float = 0.2):
        super().__init__("PSAR")
        self.af_start = af_start
        self.af_inc = af_increment
        self.af_max = af_max
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < 30: return 0
        # 简化PSAR
        high, low = df['high'], df['low']
        trend = 1
        sar = low.iloc[0]
        af = self.af_start
        
        for i in range(1, len(df)):
            prev_sar = sar
            sar = sar + af * (high.iloc[i-1] - sar)
            
            if trend == 1:
                if low.iloc[i] < sar:
                    trend = -1
                    sar = high.iloc[i-1]
                    af = self.af_start
                else:
                    if high.iloc[i] > high.iloc[i-1]:
                        af = min(af + self.af_inc, self.af_max)
            else:
                if high.iloc[i] > sar:
                    trend = 1
                    sar = low.iloc[i-1]
                    af = self.af_start
                else:
                    if low.iloc[i] < low.iloc[i-1]:
                        af = min(af + self.af_inc, self.af_max)
        
        if trend == 1: return 1
        return -1
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class IchimokuCloud(Strategy):
    """一目均衡表"""
    def __init__(self):
        super().__init__("ICHIMOKU")
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < 52: return 0
        
        high, low, close = df['high'], df['low'], df['close']
        
        # Tenkan-sen (转换线)
        tenkan = (high.rolling(9).max() + low.rolling(9).min()) / 2
        # Kijun-sen (基准线)
        kijun = (high.rolling(26).max() + low.rolling(26).min()) / 2
        # Senkou Span A (先行上线)
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        # Senkou Span B (先行下线)
        senkou_b = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
        
        if len(tenkan) < 2: return 0
        
        # 买入: 价格上穿云层
        if close.iloc[-1] > senkou_a.iloc[-1] and close.iloc[-1] > senkou_b.iloc[-1]:
            if close.iloc[-2] <= senkou_a.iloc[-2] or close.iloc[-2] <= senkou_b.iloc[-2]:
                return 1
        
        # 卖出: 价格下穿云层
        if close.iloc[-1] < senkou_a.iloc[-1] and close.iloc[-1] < senkou_b.iloc[-1]:
            if close.iloc[-2] >= senkou_a.iloc[-2] or close.iloc[-2] >= senkou_b.iloc[-2]:
                return -1
        
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 动量策略 ====================

class Momentum(Strategy):
    """动量策略"""
    def __init__(self, period: int = 12):
        super().__init__(f"MOM{period}")
        self.period = period
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        mom = df['close'].pct_change(self.period)
        
        if mom.iloc[-1] > 0.05: return 1
        if mom.iloc[-1] < -0.05: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class RSIOversold(Strategy):
    """RSI超买超卖"""
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__(f"RSI{period}")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        
        if rsi.iloc[-1] < self.oversold: return 1
        if rsi.iloc[-1] > self.overbought: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class Stochastic(Strategy):
    """随机指标"""
    def __init__(self, k: int = 14, d: int = 3):
        super().__init__(f"STOCH{k}_{d}")
        self.k = k
        self.d = d
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.k + 5: return 0
        
        low_min = df['low'].rolling(self.k).min()
        high_max = df['high'].rolling(self.k).max()
        
        k = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
        d = k.rolling(self.d).mean()
        
        if k.iloc[-1] < 20 and d.iloc[-1] < 20: return 1
        if k.iloc[-1] > 80 and d.iloc[-1] > 80: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class CCI(Strategy):
    """商品通道指标"""
    def __init__(self, period: int = 20):
        super().__init__(f"CCI{period}")
        self.period = period
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma = tp.rolling(self.period).mean()
        mad = (tp - sma).abs().rolling(self.period).mean()
        cci = (tp - sma) / (0.015 * mad + 1e-10)
        
        if cci.iloc[-1] < -100: return 1
        if cci.iloc[-1] > 100: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 突破策略 ====================

class Breakout(Strategy):
    """N日高点突破"""
    def __init__(self, period: int = 20):
        super().__init__(f"BRK{period}")
        self.period = period
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        high_max = df['high'].rolling(self.period).max()
        low_min = df['low'].rolling(self.period).min()
        
        if df['close'].iloc[-1] > high_max.shift(1).iloc[-1]: return 1
        if df['close'].iloc[-1] < low_min.shift(1).iloc[-1]: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class VolatilityBreakout(Strategy):
    """波动率突破"""
    def __init__(self, period: int = 20, multiplier: float = 2.0):
        super().__init__(f"VOLBRK{period}")
        self.period = period
        self.mult = multiplier
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        atr = (df['high'] - df['low']).rolling(self.period).mean()
        open_price = df['open'].iloc[0]
        
        if df['close'].iloc[-1] > open_price + self.mult * atr.iloc[-1]: return 1
        if df['close'].iloc[-1] < open_price - self.mult * atr.iloc[-1]: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 布林带策略 ====================

class BollingerBands(Strategy):
    """布林带策略"""
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(f"BB{period}")
        self.period = period
        self.std = std_dev
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        ma = df['close'].rolling(self.period).mean()
        std = df['close'].rolling(self.period).std()
        upper = ma + self.std * std
        lower = ma - self.std * std
        
        if df['close'].iloc[-1] < lower.iloc[-1]: return 1
        if df['close'].iloc[-1] > upper.iloc[-1]: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 均值回归 ====================

class MeanReversion(Strategy):
    """均值回归策略"""
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__(f"MR{period}")
        self.period = period
        self.std = std_dev
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        ma = df['close'].rolling(self.period).mean()
        std = df['close'].rolling(self.period).std()
        
        z_score = (df['close'] - ma) / std
        
        if z_score.iloc[-1] < -self.std: return 1
        if z_score.iloc[-1] > self.std: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 通道策略 ====================

class DonchianChannel(Strategy):
    """唐奇安通道"""
    def __init__(self, period: int = 20):
        super().__init__(f"DC{period}")
        self.period = period
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        upper = df['high'].rolling(self.period).max()
        lower = df['low'].rolling(self.period).min()
        
        if df['close'].iloc[-1] > upper.shift(1).iloc[-1]: return 1
        if df['close'].iloc[-1] < lower.shift(1).iloc[-1]: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

class KeltnerChannel(Strategy):
    """肯特纳通道"""
    def __init__(self, period: int = 20, atr_mult: float = 2.0):
        super().__init__(f"KC{period}")
        self.period = period
        self.atr_mult = atr_mult
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < self.period + 5: return 0
        
        ma = df['close'].rolling(self.period).mean()
        atr = (df['high'] - df['low']).rolling(self.period).mean()
        
        upper = ma + self.atr_mult * atr
        lower = ma - self.atr_mult * atr
        
        if df['close'].iloc[-1] < lower.iloc[-1]: return 1
        if df['close'].iloc[-1] > upper.iloc[-1]: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 综合策略 ====================

class Composite(Strategy):
    """复合策略 - 多指标确认"""
    def __init__(self):
        super().__init__("COMPOSITE")
        self.ma = MAIntersection(5, 10)
        self.rsi = RSIOversold()
        self.macd = MACDTrend()
    
    def generate_signal(self, df: pd.DataFrame) -> int:
        if len(df) < 30: return 0
        
        signals = [
            self.ma.generate_signal(df),
            self.rsi.generate_signal(df),
            self.macd.generate_signal(df)
        ]
        
        # 至少2个指标确认
        buy_votes = sum(1 for s in signals if s == 1)
        sell_votes = sum(1 for s in signals if s == -1)
        
        if buy_votes >= 2: return 1
        if sell_votes >= 2: return -1
        return 0
    
    def get_position_signal(self, df: pd.DataFrame) -> int:
        return self.generate_signal(df)

# ==================== 所有策略列表 ====================

ALL_STRATEGIES = {
    # 趋势策略
    'MA5_10': lambda: MAIntersection(5, 10),
    'MA10_20': lambda: MAIntersection(10, 20),
    'MA20_50': lambda: MAIntersection(20, 50),
    'MACD': lambda: MACDTrend(),
    'PSAR': lambda: ParabolicSAR(),
    'ICHIMOKU': lambda: IchimokuCloud(),
    
    # 动量策略
    'MOM': lambda: Momentum(12),
    'MOM5': lambda: Momentum(5),
    'MOM20': lambda: Momentum(20),
    'RSI': lambda: RSIOversold(),
    'STOCH': lambda: Stochastic(),
    'CCI': lambda: CCI(),
    
    # 突破策略
    'BRK20': lambda: Breakout(20),
    'BRK10': lambda: Breakout(10),
    'VOLBRK': lambda: VolatilityBreakout(),
    
    # 布林带
    'BB': lambda: BollingerBands(),
    
    # 均值回归
    'MR': lambda: MeanReversion(),
    
    # 通道策略
    'DC': lambda: DonchianChannel(),
    'KC': lambda: KeltnerChannel(),
    
    # 复合策略
    'COMPOSITE': lambda: Composite(),
}

def get_strategy(name: str) -> Strategy:
    """获取策略实例"""
    if name in ALL_STRATEGIES:
        return ALL_STRATEGIES[name]()
    return None

def get_all_strategies() -> list:
    """获取所有策略"""
    return [func() for func in ALL_STRATEGIES.values()]
