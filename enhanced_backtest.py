#!/usr/bin/env python3
"""
增强回测分析模块
添加专业量化指标
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import json

class EnhancedBacktest:
    """增强回测分析"""
    
    def __init__(self):
        self.results = {}
    
    def calculate_metrics(self, returns: List[float], initial_capital: float = 10000) -> Dict:
        """计算专业量化指标"""
        
        if returns is None or len(returns) == 0:
            return self._empty_metrics()
        
        returns = np.array(returns)
        
        # 基础指标
        total_return = np.sum(returns)
        avg_return = np.mean(returns)
        
        # 胜率
        win_rate = np.sum(returns > 0) / len(returns) * 100
        
        # 盈亏比
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        profit_factor = np.sum(wins) / abs(np.sum(losses)) if len(losses) > 0 and np.sum(losses) != 0 else 0
        
        # 夏普比率 (年化)
        if np.std(returns) > 0:
            sharpe = (avg_return / np.std(returns)) * np.sqrt(252)  # 年化
        else:
            sharpe = 0
        
        # 最大回撤
        cumulative = (1 + returns / 100).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max * 100
        max_drawdown = np.min(drawdown)
        
        # 卡玛比率 (年化收益/最大回撤)
        annual_return = avg_return * 252
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 索提诺比率 (只考虑下行波动)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and np.std(downside_returns) > 0:
            sortino = (avg_return / np.std(downside_returns)) * np.sqrt(252)
        else:
            sortino = 0
        
        # 盈利/亏损交易
        avg_win = np.mean(wins) if len(wins) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0
        
        return {
            'total_return': round(total_return, 2),
            'avg_return': round(avg_return, 4),
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_drawdown, 2),
            'calmar_ratio': round(calmar, 2),
            'sortino_ratio': round(sortino, 2),
            'total_trades': len(returns),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
        }
    
    def _empty_metrics(self) -> Dict:
        return {
            'total_return': 0,
            'avg_return': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'calmar_ratio': 0,
            'sortino_ratio': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'avg_win': 0,
            'avg_loss': 0,
        }
    
    def run_backtest(self, df: pd.DataFrame, strategy_func, initial_capital: float = 10000) -> Dict:
        """运行完整回测"""
        
        if df is None or len(df) < 60:
            return {'error': '数据不足'}
        
        signals = []
        prices = df['close'].values
        dates = df['date'].values if 'date' in df.columns else range(len(df))
        
        # 生成信号
        for i in range(20, len(df)):
            signal = strategy_func(df.iloc[:i+1])
            signals.append({
                'date': dates[i] if isinstance(dates[0], str) else str(i),
                'signal': signal,
                'price': prices[i]
            })
        
        # 计算收益
        returns = []
        position = 0
        entry_price = 0
        trades = []
        
        for i, s in enumerate(signals):
            if s['signal'] == 1 and position == 0:  # 买入
                position = 1
                entry_price = s['price']
                entry_date = s['date']
            elif s['signal'] == -1 and position == 1:  # 卖出
                ret = (s['price'] - entry_price) / entry_price * 100
                returns.append(ret)
                trades.append({
                    'entry_date': entry_date,
                    'exit_date': s['date'],
                    'return': ret,
                    'type': 'win' if ret > 0 else 'loss'
                })
                position = 0
        
        # 持有到结束
        if position == 1 and entry_price > 0:
            ret = (prices[-1] - entry_price) / entry_price * 100
            returns.append(ret)
        
        # 计算指标
        metrics = self.calculate_metrics(returns, initial_capital)
        metrics['trades'] = trades
        
        return metrics
    
    def generate_report(self, metrics: Dict) -> str:
        """生成回测报告"""
        
        report = f"""
╔══════════════════════════════════════════════════════════╗
║                    回测分析报告                            ║
╠══════════════════════════════════════════════════════════╣
║  收益指标                                                  ║
║  ───────────────────────────────────────────────────────  ║
║  总收益率:     {metrics.get('total_return', 0):>8.2f}%                        ║
║  平均收益:     {metrics.get('avg_return', 0):>8.4f}%                        ║
║  交易次数:     {metrics.get('total_trades', 0):>8d}                          ║
╠══════════════════════════════════════════════════════════╣
║  风险指标                                                  ║
║  ───────────────────────────────────────────────────────  ║
║  夏普比率:    {metrics.get('sharpe_ratio', 0):>8.2f}                        ║
║  最大回撤:    {metrics.get('max_drawdown', 0):>8.2f}%                        ║
║  卡玛比率:    {metrics.get('calmar_ratio', 0):>8.2f}                        ║
║  索提诺比率:  {metrics.get('sortino_ratio', 0):>8.2f}                        ║
╠══════════════════════════════════════════════════════════╣
║  交易统计                                                  ║
║  ───────────────────────────────────────────────────────  ║
║  胜率:        {metrics.get('win_rate', 0):>8.2f}%                        ║
║  盈利交易:    {metrics.get('winning_trades', 0):>8d}                          ║
║  亏损交易:    {metrics.get('losing_trades', 0):>8d}                          ║
║  盈亏比:      {metrics.get('profit_factor', 0):>8.2f}                        ║
║  平均盈利:    {metrics.get('avg_win', 0):>8.2f}%                        ║
║  平均亏损:    {metrics.get('avg_loss', 0):>8.2f}%                        ║
╚══════════════════════════════════════════════════════════╝
"""
        return report


# 测试
if __name__ == "__main__":
    import numpy as np
    
    # 模拟收益数据
    returns = np.random.normal(0.5, 2, 100)
    
    bt = EnhancedBacktest()
    metrics = bt.calculate_metrics(returns)
    
    print(bt.generate_report(metrics))
