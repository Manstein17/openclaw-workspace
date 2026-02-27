#!/usr/bin/env python3
"""
每周系统改进分析
分析交易数据，发现系统问题，提出改进建议
"""
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

LOG_DIR = "/Users/manstein17/.openclaw/workspace/trading_logs"

class WeeklyAnalyzer:
    """每周分析器"""
    
    def __init__(self):
        self.today = datetime.now()
    
    def get_week_logs(self) -> list:
        """获取本周日志"""
        logs = []
        for i in range(7):
            date = (self.today - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = f"{LOG_DIR}/{date}.json"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs.append(json.load(f))
        return logs
    
    def analyze_trades(self, logs: list) -> dict:
        """分析交易数据"""
        all_trades = []
        for log in logs:
            all_trades.extend(log.get('trades', []))
        
        if not all_trades:
            return {"error": "本周无交易"}
        
        # 统计买卖方向
        buy_count = sum(1 for t in all_trades if t.get('type') == 'BUY')
        sell_count = sum(1 for t in all_trades if t.get('type') == 'SELL')
        
        return {
            "total": len(all_trades),
            "buy": buy_count,
            "sell": sell_count,
            "trades": all_trades
        }
    
    def analyze_positions(self, logs: list) -> dict:
        """分析持仓表现"""
        position_performance = defaultdict(list)
        
        for log in logs:
            positions = log.get('positions', {})
            for symbol, pos in positions.items():
                pnl = pos.get('pnl', 0)
                position_performance[symbol].append(pnl)
        
        # 计算每只股票的平均收益
        avg_performance = {}
        for symbol, pnls in position_performance.items():
            avg_performance[symbol] = np.mean(pnls) if pnls else 0
        
        return avg_performance
    
    def find_problems(self, logs: list) -> list:
        """发现问题"""
        problems = []
        
        if len(logs) < 2:
            return ["数据不足，无法分析"]
        
        # 检查是否有亏损
        latest = logs[0]
        positions = latest.get('positions', {})
        
        for symbol, pos in positions.items():
            pnl = pos.get('pnl', 0)
            if pnl < -3:
                problems.append(f"持仓{symbol}亏损{pnl:.1f}%，建议检查止损")
            elif pnl < 0:
                problems.append(f"持仓{symbol}亏损{pnl:.1f}%，关注")
        
        # 检查交易频率
        total_trades = sum(len(log.get('trades', [])) for log in logs)
        if total_trades > 20:
            problems.append(f"本周交易{total_trades}笔，频率偏高")
        
        # 检查持仓集中度
        if len(positions) > 0:
            total_value = sum(p.get('current_price', 0) * p.get('shares', 0) for p in positions.values())
            for symbol, pos in positions.items():
                pos_value = pos.get('current_price', 0) * pos.get('shares', 0)
                if total_value > 0 and pos_value / total_value > 0.5:
                    problems.append(f"持仓{symbol}占比过高，注意分散风险")
        
        if not problems:
            problems.append("本周系统运行正常，未发现明显问题")
        
        return problems
    
    def suggest_improvements(self, logs: list) -> list:
        """建议改进"""
        suggestions = []
        
        # 基于数据给出建议
        if not logs:
            suggestions.append("开始交易后才有改进建议")
            return suggestions
        
        # 检查胜率
        trade_analysis = self.analyze_trades(logs)
        if "error" not in trade_analysis and trade_analysis.get("total", 0) > 0:
            if trade_analysis["sell"] > 0:
                # 简单判断：如果卖的时候大多亏钱
                suggestions.append("建议优化卖出策略，考虑设置止盈止损")
        
        # 检查持仓时间
        suggestions.append("当前策略适合日线级别，可考虑加入更短期信号")
        
        # 风控建议
        suggestions.append("建议每周检查组合相关性，避免过度集中")
        
        return suggestions
    
    def generate_report(self) -> str:
        """生成周报"""
        logs = self.get_week_logs()
        
        if not logs:
            return """
=== 本周总结 ===
本周暂无交易数据，系统正在运行中。
"""
        
        # 基础统计
        total_value = logs[0].get('portfolio_value', 0) + logs[0].get('cash', 0)
        if len(logs) >= 2:
            prev_value = logs[-1].get('portfolio_value', 0) + logs[-1].get('cash', 0)
            week_return = (total_value - prev_value) / prev_value * 100 if prev_value > 0 else 0
        else:
            week_return = 0
        
        trade_analysis = self.analyze_trades(logs)
        problems = self.find_problems(logs)
        suggestions = self.suggest_improvements(logs)
        
        report = f"""
=====================================
📅 本周交易总结 ({logs[0].get('date', '')} ~ {logs[-1].get('date', '')})
=====================================

📊 基础数据
- 当前总资产: ¥{total_value:,.2f}
- 本周收益: {week_return:+.2f}%
- 交易笔数: {trade_analysis.get('total', 0)}

⚠️ 发现问题
"""
        for p in problems:
            report += f"- {p}\n"
        
        report += """
💡 改进建议
"""
        for s in suggestions:
            report += f"- {s}\n"
        
        report += """
=====================================
"""
        
        return report
    
    def save_report(self) -> str:
        """保存周报"""
        report = self.generate_report()
        week_file = f"{LOG_DIR}/week_{self.today.strftime('%Y-%W')}.txt"
        
        with open(week_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return week_file


# 测试
if __name__ == "__main__":
    analyzer = WeeklyAnalyzer()
    print(analyzer.generate_report())
