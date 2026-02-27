#!/bin/bash
# 定时任务脚本
# 设置crontab:
# 0 8 * * * cd ~/.openclaw/workspace && source venv/bin/activate && python daily_runner.py
# 0 15 * * * cd ~/.openclaw/workspace && source venv/bin/activate && python daily_runner.py
"""

import os
import sys
import json
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from trading_system_pro import TradingSystemPro
from ai_policy_analyzer import AIPolicyAnalyzer
from policy_scheduler import PolicyMonitor

class DailyRunner:
    """每日运行器"""
    
    def __init__(self):
        self.policy_monitor = PolicyMonitor()
    
    def run_morning(self):
        """早间运行 (8点)"""
        print("\n" + "="*60)
        print(f"🕗 早间任务 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        # 1. 检查新政策
        print("\n📰 检查政策...")
        if self.policy_monitor.has_new_policy():
            print("发现新政策，进行AI分析...")
            try:
                analyzer = AIPolicyAnalyzer()
                policy_result = analyzer.analyze_daily_policy()
                print(f"政策分析: {policy_result.get('利好板块', [])}")
            except Exception as e:
                print(f"政策分析失败: {e}")
        else:
            print("无新政策")
        
        # 2. 运行交易系统
        print("\n📈 运行交易系统...")
        try:
            system = TradingSystemPro()
            system.run()
        except Exception as e:
            print(f"交易系统错误: {e}")
    
    def run_afternoon(self):
        """午间运行 (15点)"""
        print("\n" + "="*60)
        print(f"🕒 午间任务 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*60)
        
        # 下午主要检查持仓和风控
        print("\n📈 运行交易系统...")
        try:
            system = TradingSystemPro()
            system.run()
        except Exception as e:
            print(f"交易系统错误: {e}")

# ============== 主程序 ==============
if __name__ == '__main__':
    runner = DailyRunner()
    
    hour = datetime.now().hour
    
    if 7 <= hour <= 9:
        runner.run_morning()
    elif 14 <= hour <= 16:
        runner.run_afternoon()
    else:
        print(f"当前时间 {hour}点，不在运行时间(8点或15点)")
        print("手动运行...")
        runner.run_morning()
