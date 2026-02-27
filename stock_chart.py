#!/usr/bin/env python3
"""
专业图表生成模块
K线图、技术指标可视化
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
# from matplotlib.patches import Candlestick
import pandas as pd
import numpy as np
from datetime import datetime
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class StockChart:
    """股票图表生成器"""
    
    def __init__(self):
        self.chart_dir = os.path.expanduser("~/.openclaw/workspace/charts")
        os.makedirs(self.chart_dir, exist_ok=True)
    
    def plot_kline_with_ma(self, df: pd.DataFrame, symbol: str = "", days: int = 60) -> str:
        """绘制K线图+均线"""
        
        if df is None or len(df) < 30:
            return ""
        
        # 取最近数据
        df = df.tail(days).copy()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # K线
        for i, row in df.iterrows():
            color = 'red' if row['close'] >= row['open'] else 'green'
            ax.plot([i, i], [row['low'], row['high']], color=color, linewidth=0.5)
            ax.plot([i, i], [row['open'], row['close']], color=color, linewidth=2)
        
        # 均线
        if 'close' in df.columns:
            ma5 = df['close'].rolling(5).mean()
            ma10 = df['close'].rolling(10).mean()
            ma20 = df['close'].rolling(20).mean()
            
            ax.plot(range(len(df)), ma5, label='MA5', linewidth=1.5, color='yellow')
            ax.plot(range(len(df)), ma10, label='MA10', linewidth=1.5, color='purple')
            ax.plot(range(len(df)), ma20, label='MA20', linewidth=1.5, color='blue')
        
        ax.legend(loc='upper left')
        ax.set_title(f'{symbol} K线图', fontsize=14)
        ax.set_xlabel('交易日')
        ax.set_ylabel('价格')
        
        # 保存
        filename = f"{self.chart_dir}/{symbol}_kline.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def plot_bollinger_bands(self, df: pd.DataFrame, symbol: str = "", days: int = 60) -> str:
        """绘制布林带"""
        
        df = df.tail(days).copy()
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # 收盘价
        ax.plot(range(len(df)), df['close'], label='收盘价', linewidth=1.5, color='black')
        
        # 布林带
        ma = df['close'].rolling(20).mean()
        std = df['close'].rolling(20).std()
        upper = ma + 2 * std
        lower = ma - 2 * std
        
        ax.plot(range(len(df)), upper, label='上轨', linewidth=1, color='red', linestyle='--')
        ax.plot(range(len(df)), ma, label='中轨', linewidth=1, color='blue')
        ax.plot(range(len(df)), lower, label='下轨', linewidth=1, color='green', linestyle='--')
        ax.fill_between(range(len(df)), upper, lower, alpha=0.1)
        
        ax.legend()
        ax.set_title(f'{symbol} 布林带', fontsize=14)
        
        filename = f"{self.chart_dir}/{symbol}_bb.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def plot_macd(self, df: pd.DataFrame, symbol: str = "", days: int = 60) -> str:
        """绘制MACD"""
        
        df = df.tail(days).copy()
        
        # 计算MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
        
        # 价格
        ax1.plot(range(len(df)), df['close'], label='价格', linewidth=1.5)
        ax1.set_title(f'{symbol} MACD', fontsize=14)
        
        # MACD
        ax2.bar(range(len(df)), histogram, label='柱状', color=['red' if h > 0 else 'green' for h in histogram])
        ax2.plot(range(len(df)), macd, label='DIF', linewidth=1, color='blue')
        ax2.plot(range(len(df)), signal, label='DEA', linewidth=1, color='orange')
        
        ax2.legend()
        
        filename = f"{self.chart_dir}/{symbol}_macd.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def plot_portfolio_performance(self, equity_curve: list, trades: list = None) -> str:
        """绘制组合收益曲线"""
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        
        # 权益曲线
        ax1.plot(equity_curve, linewidth=2, color='blue')
        ax1.fill_between(range(len(equity_curve)), equity_curve, alpha=0.3)
        ax1.set_title('组合权益曲线', fontsize=14)
        ax1.set_ylabel('资产净值')
        
        # 回撤
        if len(equity_curve) > 0:
            running_max = np.maximum.accumulate(equity_curve)
            drawdown = (np.array(equity_curve) - running_max) / running_max * 100
            ax2.fill_between(range(len(drawdown)), drawdown, color='red', alpha=0.5)
            ax2.set_title('回撤', fontsize=14)
            ax2.set_ylabel('回撤%')
        
        filename = f"{self.chart_dir}/portfolio_performance.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def generate_all_charts(self, df: pd.DataFrame, symbol: str) -> dict:
        """生成所有图表"""
        
        charts = {}
        
        try:
            kline = self.plot_kline_with_ma(df, symbol)
            if kline:
                charts['kline'] = kline
            
            bb = self.plot_bollinger_bands(df, symbol)
            if bb:
                charts['bollinger'] = bb
            
            macd = self.plot_macd(df, symbol)
            if macd:
                charts['macd'] = macd
                
        except Exception as e:
            print(f"图表生成错误: {e}")
        
        return charts


# 测试
if __name__ == "__main__":
    import numpy as np
    
    # 模拟数据
    dates = pd.date_range('2025-01-01', periods=100)
    close = 100 + np.cumsum(np.random.randn(100))
    
    df = pd.DataFrame({
        'date': dates,
        'open': close + np.random.randn(100),
        'high': close + abs(np.random.randn(100)) * 2,
        'low': close - abs(np.random.randn(100)) * 2,
        'close': close,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    chart = StockChart()
    charts = chart.generate_all_charts(df, 'TEST')
    print(f"生成图表: {list(charts.keys())}")
