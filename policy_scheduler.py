"""
政策监控定时任务
- 早上8点、下午3点检查新政策
- 有新政策才进行AI分析
- 整合到主系统
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# 配置
POLICY_CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/policy_cache")
os.makedirs(POLICY_CACHE_DIR, exist_ok=True)

class PolicyMonitor:
    """政策监控器"""
    
    def __init__(self):
        self.last_policy_file = os.path.join(POLICY_CACHE_DIR, "last_policy.json")
        self.analysis_file = os.path.join(POLICY_CACHE_DIR, "daily_analysis.json")
    
    def get_last_policy(self) -> dict:
        """获取上次政策"""
        if os.path.exists(self.last_policy_file):
            with open(self.last_policy_file, 'r') as f:
                return json.load(f)
        return {'date': '', 'summary': ''}
    
    def save_policy(self, policy: dict):
        """保存政策"""
        with open(self.last_policy_file, 'w') as f:
            json.dump(policy, f, ensure_ascii=False, indent=2)
    
    def check_new_policy(self) -> bool:
        """检查是否有新政策"""
        # 简单比较：今天的日期
        today = datetime.now().strftime('%Y-%m-%d')
        last = self.get_last_policy()
        
        # 如果上次政策日期是今天，说明已经分析过了
        if last.get('date') == today:
            return False
        
        return True
    
    def has_new_policy(self) -> bool:
        """判断是否有新政策需要分析"""
        # 方式1: 每天首次检查
        if not self.check_new_policy():
            print(f"今日({datetime.now().strftime('%Y-%m-%d')})已分析政策，跳过")
            return False
        
        # 方式2: 检测是否有重大政策（简化版：检查文件时间）
        # 实际可以接入更多数据源
        
        return True
    
    def mark_analyzed(self):
        """标记已分析"""
        policy = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'analyzed': True,
            'timestamp': datetime.now().isoformat()
        }
        self.save_policy(policy)
    
    def should_run(self, hour: int) -> bool:
        """判断当前时间是否应该运行"""
        current_hour = datetime.now().hour
        
        # 设置的时间点
        target_hours = [hour]  # 可以设置多个时间点
        
        if current_hour == hour:
            # 检查是否已经运行过
            last = self.get_last_policy()
            last_date = last.get('date', '')
            today = datetime.now().strftime('%Y-%m-%d')
            
            if last_date != today:
                return True
        
        return False

# ============== 定时检查 ==============
def run_policy_check():
    """运行政策检查"""
    from ai_policy_analyzer import AIPolicyAnalyzer
    
    monitor = PolicyMonitor()
    
    # 检查是否需要运行
    if not monitor.has_new_policy():
        print("今日无需分析政策")
        return None
    
    print("检测到新政策，开始AI分析...")
    
    # 运行AI分析
    analyzer = AIPolicyAnalyzer()
    result = analyzer.analyze_daily_policy()
    
    # 保存结果
    with open(monitor.analysis_file, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 标记已分析
    monitor.mark_analyzed()
    
    return result

# ============== 主程序 ==============
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            run_policy_check()
        elif sys.argv[1] == 'test':
            monitor = PolicyMonitor()
            print(f"今日已分析: {not monitor.has_new_policy()}")
    else:
        # 手动运行
        print("="*50)
        print("政策监控")
        print("="*50)
        
        monitor = PolicyMonitor()
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"上次分析: {monitor.get_last_policy().get('date', '从未')}")
        
        # 检查是否需要运行
        # 早上8点检查
        if monitor.should_run(8):
            print("\n🕗 早上8点检查...")
            result = run_policy_check()
            if result:
                print(f"\n利好板块: {result.get('利好板块', [])}")
        
        # 下午3点检查
        elif monitor.should_run(15):
            print("\n🕒 下午3点检查...")
            result = run_policy_check()
            if result:
                print(f"\n利好板块: {result.get('利好板块', [])}")
        
        else:
            print("\n当前时间不是检查时间点")
