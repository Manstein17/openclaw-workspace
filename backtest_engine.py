"""
回测引擎模块
- 历史数据回测
- 策略评估
- 风险指标计算
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
    
    def run_backtest(self, df: pd.DataFrame, strategy_class, 
                     stop_loss: float = 0.05, 
                     take_profit: float = 0.10,
                     position_size: float = 0.3) -> Dict:
        """运行回测"""
        if df is None or len(df) < 120:
            return None
        
        # 创建策略实例
        strategy = strategy_class()
        
        # 模拟交易
        capital = self.initial_capital
        position = 0
        entry_price = 0
        
        trades = []
        equity_curve = []
        
        # 逐日计算信号
        for i in range(50, len(df)):  # 预热50天
            row = df.iloc[i]
            date = row['date']
            price = row['close']
            
            # 获取信号
            test_df = df.iloc[:i+1]
            signal = strategy.generate_signal(test_df)
            
            # 记录权益
            if position > 0:
                value = capital + position * price
            else:
                value = capital
            equity_curve.append({'date': date, 'value': value})
            
            # 买入
            if signal == 1 and position == 0:
                shares = int((capital * position_size) / price)
                if shares > 0:
                    capital -= shares * price
                    position = shares
                    entry_price = price
            
            # 卖出
            elif position > 0:
                should_sell = False
                reason = ''
                
                if signal == -1:
                    should_sell = True
                    reason = '信号反转'
                
                profit_pct = (price - entry_price) / entry_price
                
                if profit_pct <= -stop_loss:
                    should_sell = True
                    reason = f'止损({profit_pct*100:.1f}%)'
                elif profit_pct >= take_profit:
                    should_sell = True
                    reason = f'止盈({profit_pct*100:.1f}%)'
                
                if should_sell:
                    capital += position * price
                    trades.append({
                        'entry_price': entry_price,
                        'exit_price': price,
                        'profit_pct': profit_pct * 100,
                        'reason': reason
                    })
                    position = 0
        
        # 计算指标
        return self.calculate_metrics(trades, equity_curve)
    
    def calculate_metrics(self, trades: List, equity_curve: List) -> Dict:
        """计算风险指标"""
        if not trades:
            return {
                'total_return': 0,
                'win_rate': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'trades': 0
            }
        
        # 总收益率
        final_value = equity_curve[-1]['value'] if equity_curve else self.initial_capital
        total_return = (final_value - self.initial_capital) / self.initial_capital * 100
        
        # 胜率
        wins = sum(1 for t in trades if t['profit_pct'] > 0)
        win_rate = wins / len(trades) * 100 if trades else 0
        
        # 夏普比率
        returns = [t['profit_pct'] for t in trades]
        if len(returns) > 1 and np.std(returns) > 0:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252/20)
        else:
            sharpe = 0
        
        # 最大回撤
        max_value = self.initial_capital
        max_drawdown = 0
        for eq in equity_curve:
            if eq['value'] > max_value:
                max_value = eq['value']
            dd = (max_value - eq['value']) / max_value * 100
            if dd > max_drawdown:
                max_drawdown = dd
        
        return {
            'total_return': total_return,
            'win_rate': win_rate,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'trades': len(trades),
            'wins': wins,
            'losses': len(trades) - wins,
            'final_value': final_value
        }

def run_backtest(stocks: List, years: int = 1) -> List:
    """回测股票池"""
    from trading_system_final import DataSource, MAStrategy, RSIStrategy, MACDStrategy
    
    ds = DataSource()
    engine = BacktestEngine()
    
    strategies = [MAStrategy, RSIStrategy, MACDStrategy]
    strategy_names = ['MA', 'RSI', 'MACD']
    
    results = []
    
    print("="*60)
    print(f"回测 ({years}年)")
    print("="*60)
    
    for symbol, name, industry, _, _ in stocks:
        print(f"回测 {name}...", end=" ")
        
        df = ds.load_data(symbol)
        if df is None or len(df) < 120:
            print("数据不足")
            continue
        
        # 筛选年份
        cutoff = datetime.now() - timedelta(days=years*365)
        df = df[df['date'] >= pd.to_datetime(cutoff)]
        
        if len(df) < 120:
            print("数据不足")
            continue
        
        # 测试各策略
        best_result = None
        best_return = -999
        
        for strategy, sname in zip(strategies, strategy_names):
            result = engine.run_backtest(df.copy(), strategy)
            if result:
                result['strategy'] = sname
                if result['total_return'] > best_return:
                    best_return = result['total_return']
                    best_result = result
        
        if best_result:
            print(f"最优: {best_result['strategy']} {best_result['total_return']:+.1f}% "
                  f"夏普:{best_result['sharpe_ratio']:.2f} 回撤:{best_result['max_drawdown']:.1f}%")
            
            results.append({
                'symbol': symbol,
                'name': name,
                'industry': industry,
                'best_strategy': best_result['strategy'],
                'return': best_result['total_return'],
                'sharpe': best_result['sharpe_ratio'],
                'drawdown': best_result['max_drawdown'],
                'winrate': best_result['win_rate'],
                'trades': best_result['trades']
            })
        else:
            print("无结果")
    
    return results

def generate_report(results: List):
    """生成回测报告"""
    if not results:
        print("无回测结果")
        return
    
    print("\n" + "="*60)
    print("回测报告")
    print("="*60)
    
    total = len(results)
    profitable = sum(1 for r in results if r['return'] > 0)
    
    print(f"\n📊 统计:")
    print(f"   回测股票: {total}只")
    print(f"   盈利: {profitable}只 ({profitable/total*100:.1f}%)")
    print(f"   亏损: {total-profitable}只 ({(total-profitable)/total*100:.1f}%)")
    
    # 平均
    avg_return = sum(r['return'] for r in results) / total
    avg_sharpe = sum(r['sharpe'] for r in results) / total
    avg_dd = sum(r['drawdown'] for r in results) / total
    
    print(f"\n📈 平均表现:")
    print(f"   收益率: {avg_return:+.1f}%")
    print(f"   夏普比率: {avg_sharpe:.2f}")
    print(f"   最大回撤: {avg_dd:.1f}%")
    
    # Top 5
    results.sort(key=lambda x: x['return'], reverse=True)
    
    print("\n🏆 Top 5:")
    for i, r in enumerate(results[:5], 1):
        print(f"   {i}. {r['name']}: {r['return']:+.1f}% ({r['best_strategy']}) "
              f"夏普:{r['sharpe']:.2f}")
    
    # 推荐
    print("\n✅ 推荐股票 (高夏普+低回撤):")
    results.sort(key=lambda x: x['sharpe'], reverse=True)
    for r in results:
        if r['sharpe'] > 0.5 and r['drawdown'] < 25:
            print(f"   {r['name']}: 策略={r['best_strategy']} "
                  f"收益={r['return']:+.1f}% 夏普={r['sharpe']:.2f}")

# ============== 测试 ==============
if __name__ == '__main__':
    stocks = [
        ('600519', '贵州茅台', '白酒', 20, 40),
        ('601318', '中国平安', '保险', 8, 15),
        ('300750', '宁德时代', '新能源', 15, 30),
        ('600036', '招商银行', '银行', 5, 10),
        ('000858', '五粮液', '白酒', 15, 35),
        ('600276', '恒瑞医药', '医药', 20, 40),
    ]
    
    results = run_backtest(stocks, years=1)
    generate_report(results)
