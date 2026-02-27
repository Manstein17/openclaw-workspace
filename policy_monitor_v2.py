"""
政策监控升级版 v2
- 基于时间触发（新交易日）
- 可手动触发
- 避免重复分析
"""
import os
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# 配置
POLICY_CACHE_DIR = os.path.expanduser("~/.openclaw/workspace/policy_cache")
os.makedirs(POLICY_CACHE_DIR, exist_ok=True)

class PolicyMonitor:
    """政策监控器 - 支持每日2次分析"""
    
    def __init__(self):
        self.cache_dir = Path(POLICY_CACHE_DIR)
        self.state_file = self.cache_dir / "policy_state.json"
    
    def load_state(self) -> dict:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'last_analysis_date': '',
            'morning_analyzed': False,   # 早上已分析
            'afternoon_analyzed': False,  # 下午已分析
            'analysis_count': 0
        }
    
    def save_state(self, state: dict):
        """保存状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def should_analyze(self, is_morning: bool = None) -> dict:
        """
        判断是否需要分析
        - is_morning=True: 早上8点检查
        - is_morning=False: 下午3点检查
        """
        state = self.load_state()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 判断当前时段
        if is_morning is None:
            hour = datetime.now().hour
            is_morning = hour < 12
        
        # 检查日期是否变化（新交易日）
        if state.get('last_analysis_date') != today:
            # 新交易日，重置状态
            state['last_analysis_date'] = today
            state['morning_analyzed'] = False
            state['afternoon_analyzed'] = False
            self.save_state(state)
        
        if is_morning:
            # 早上检查
            if not state.get('morning_analyzed', False):
                return {
                    'should_analyze': True,
                    'period': '早上',
                    'reason': f"今日({today})早上首次分析"
                }
            else:
                return {
                    'should_analyze': False,
                    'period': '早上',
                    'reason': f"今日({today})早上已分析过，跳过"
                }
        else:
            # 下午检查
            if not state.get('afternoon_analyzed', False):
                return {
                    'should_analyze': True,
                    'period': '下午',
                    'reason': f"今日({today})下午首次分析"
                }
            else:
                return {
                    'should_analyze': False,
                    'period': '下午',
                    'reason': f"今日({today})下午已分析过，跳过"
                }
    
    def mark_analyzed(self, period: str):
        """标记已分析"""
        state = self.load_state()
        today = datetime.now().strftime('%Y-%m-%d')
        state['last_analysis_date'] = today
        state['analysis_count'] = state.get('analysis_count', 0) + 1
        
        if period == '早上':
            state['morning_analyzed'] = True
        elif period == '下午':
            state['afternoon_analyzed'] = True
        
        self.save_state(state)
    
    def get_status(self) -> dict:
        """获取状态"""
        state = self.load_state()
        today = datetime.now().strftime('%Y-%m-%d')
        
        return {
            '上次分析': state.get('last_analysis_date', '从未'),
            '今日': today,
            '已分析次数': state.get('analysis_count', 0),
            '今日是否分析': state.get('last_analysis_date') == today
        }

# ============== 测试 ==============
if __name__ == '__main__':
    monitor = PolicyMonitor()
    
    print("="*60)
    print("政策监控状态 (每日2次)")
    print("="*60)
    
    status = monitor.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    # 测试早上
    print("\n--- 早上检查 ---")
    result = monitor.should_analyze(is_morning=True)
    print(f"  需要分析: {result['should_analyze']}")
    print(f"  时段: {result['period']}")
    print(f"  原因: {result['reason']}")
    
    if result['should_analyze']:
        monitor.mark_analyzed(result['period'])
        print("  → 已标记为已分析")
    
    # 测试下午（同一日）
    print("\n--- 下午检查 ---")
    result2 = monitor.should_analyze(is_morning=False)
    print(f"  需要分析: {result2['should_analyze']}")
    print(f"  时段: {result2['period']}")
    print(f"  原因: {result2['reason']}")
    
    if result2['should_analyze']:
        monitor.mark_analyzed(result2['period'])
        print("  → 已标记为已分析")
    
    # 再次检查（应该跳过）
    print("\n--- 再次检查(下午) ---")
    result3 = monitor.should_analyze(is_morning=False)
    print(f"  需要分析: {result3['should_analyze']}")
    print(f"  原因: {result3['reason']}")
