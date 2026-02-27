#!/usr/bin/env python3
"""
交易日志模块
记录每日交易、持仓、收益，复盘分析
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

LOG_DIR = "/Users/manstein17/.openclaw/workspace/trading_logs"

class TradingJournal:
    """交易日志"""
    
    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def save_daily_log(self, trades: List[Dict], positions: Dict, portfolio_value: float, cash: float, data_source=None):
        """保存每日交易日志"""
        log_file = f"{LOG_DIR}/{self.today}.json"
        
        # 处理positions
        positions_data = {}
        for symbol, pos in positions.items():
            current_price = pos.entry_price  # 默认用入场价
            pnl = 0
            if hasattr(pos, 'entry_price') and pos.entry_price > 0:
                pnl = (current_price - pos.entry_price) / pos.entry_price * 100
            
            positions_data[symbol] = {
                "name": getattr(pos, 'name', symbol),
                "shares": getattr(pos, 'shares', 0),
                "entry_price": getattr(pos, 'entry_price', 0),
                "current_price": current_price,
                "pnl": pnl
            }
        
        log_data = {
            "date": self.today,
            "trades": trades,
            "positions": positions_data,
            "portfolio_value": portfolio_value,
            "cash": cash,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        return log_file
    
    def get_daily_log(self, date: str = None) -> Dict:
        """获取指定日期日志"""
        if date is None:
            date = self.today
        
        log_file = f"{LOG_DIR}/{date}.json"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get_history(self, days: int = 30) -> List[Dict]:
        """获取历史日志"""
        logs = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log = self.get_daily_log(date)
            if log:
                logs.append(log)
        return logs
    
    def calculate_performance(self, days: int = 30) -> Dict:
        """计算收益率统计"""
        logs = self.get_history(days)
        
        if not logs:
            return {"error": "无历史数据"}
        
        # 计算每日收益
        daily_returns = []
        initial_value = logs[-1].get('portfolio_value', 0) + logs[-1].get('cash', 0)
        
        for i, log in enumerate(logs):
            pv = log.get('portfolio_value', 0)
            cash = log.get('cash', 0)
            total = pv + cash
            
            if i > 0:
                prev_total = logs[i-1].get('portfolio_value', 0) + logs[i-1].get('cash', 0)
                if prev_total > 0:
                    daily_return = (total - prev_total) / prev_total * 100
                    daily_returns.append(daily_return)
        
        # 统计
        if daily_returns:
            avg_return = sum(daily_returns) / len(daily_returns)
            win_days = sum(1 for r in daily_returns if r > 0)
            win_rate = win_days / len(daily_returns) * 100 if daily_returns else 0
            
            return {
                "days": len(logs),
                "avg_return": avg_return,
                "win_rate": win_rate,
                "total_return": (logs[0].get('portfolio_value', 0) + logs[0].get('cash', 0) - initial_value) / initial_value * 100 if initial_value > 0 else 0,
                "best_day": max(daily_returns) if daily_returns else 0,
                "worst_day": min(daily_returns) if daily_returns else 0
            }
        
        return {"error": "数据不足"}
    
    def generate_daily_report(self) -> str:
        """生成每日报告"""
        log = self.get_daily_log()
        
        if not log:
            return "今日无交易记录"
        
        report = f"""
=== {self.today} 每日交易报告 ===

📊 账户情况
- 总资产: ¥{log.get('portfolio_value', 0):.2f}
- 现金: ¥{log.get('cash', 0):.2f}

📈 持仓情况
"""
        positions = log.get('positions', {})
        for symbol, pos in positions.items():
            pnl = pos.get('pnl', 0)
            emoji = "🟢" if pnl > 0 else "🔴"
            report += f"- {pos['name']}: {pnl:+.2f}% {emoji}\n"
        
        trades = log.get('trades', [])
        if trades:
            report += f"\n🔄 今日交易: {len(trades)}笔\n"
        
        return report
    
    def generate_weekly_report(self) -> str:
        """生成每周报告"""
        logs = self.get_history(7)
        
        if not logs:
            return "本周无数据"
        
        # 统计
        total_trades = sum(len(log.get('trades', [])) for log in logs)
        
        # 收益变化
        if len(logs) >= 2:
            first_value = logs[0].get('portfolio_value', 0) + logs[0].get('cash', 0)
            last_value = logs[-1].get('portfolio_value', 0) + logs[-1].get('cash', 0)
            week_return = (last_value - first_value) / first_value * 100 if first_value > 0 else 0
        else:
            week_return = 0
        
        report = f"""
=== 本周交易总结 ===

📈 收益情况
- 本周收益: {week_return:+.2f}%
- 交易笔数: {total_trades}

📊 每日详情
"""
        for log in logs:
            date = log.get('date', '')
            pv = log.get('portfolio_value', 0)
            cash = log.get('cash', 0)
            trades = len(log.get('trades', []))
            report += f"- {date}: 总资产¥{pv+cash:.0f}, 交易{trades}笔\n"
        
        return report


# 测试
if __name__ == "__main__":
    journal = TradingJournal()
    print(journal.generate_daily_report())
    print(journal.generate_weekly_report())
