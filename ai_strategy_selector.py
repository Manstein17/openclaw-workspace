"""
AI策略选择器
根据市场环境自动选择最适合的策略
"""
import requests
from datetime import datetime

# MiniMax API配置
MINIMAX_API_KEY = "sk-api-1AFALQluMHGe0SU5dl84QpbUXTLXjEOBZq-4mwjvCakyi-9NPvuTdCUMWJC6OmGnhVKirRC5grvnlOhlm-Ugm_YKCJnqLHLl8e0jYZXZsxtVDQm23PAOlEQ"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"

# 所有可用策略
ALL_STRATEGY_NAMES = [
    "MA5_10", "MA10_20", "MA20_50", "MACD", "PSAR", "ICHIMOKU",
    "MOM", "MOM5", "MOM20", "RSI", "STOCH", "CCI",
    "BRK20", "BRK10", "VOLBRK", "BB", "MR", "DC", "KC", "COMPOSITE"
]

class AIStrategySelector:
    """AI策略选择器"""
    
    def __init__(self):
        self.api_key = MINIMAX_API_KEY
    
    def analyze_market_environment(self, df, industry: str) -> dict:
        """分析市场环境"""
        if df is None or len(df) < 30:
            return {'trend': '震荡', 'volatility': '中等', 'recommendation': '均线'}
        
        # 简单技术指标
        close = df['close']
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        
        # 趋势判断
        if ma5.iloc[-1] > ma20.iloc[-1] * 1.02:
            trend = '上涨'
        elif ma5.iloc[-1] < ma20.iloc[-1] * 0.98:
            trend = '下跌'
        else:
            trend = '震荡'
        
        # 波动率
        returns = close.pct_change().dropna()
        vol = returns.std()
        
        if vol > 0.03:
            volatility = '高'
        elif vol > 0.015:
            volatility = '中等'
        else:
            volatility = '低'
        
        return {'trend': trend, 'volatility': volatility}
    
    def call_ai(self, prompt: str) -> str:
        """调用MiniMax API"""
        url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-M2.5",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
        except:
            pass
        
        return ""
    
    def select_strategy(self, df, industry: str, policy_result: dict = None) -> list:
        """AI选择最佳策略"""
        
        # 1. 分析市场环境
        env = self.analyze_market_environment(df, industry)
        
        # 2. 构建prompt
        trend = env['trend']
        vol = env['volatility']
        
        # 政策信息
        policy_info = ""
        if policy_result:
            bullish = policy_result.get('利好板块', [])
            bearish = policy_result.get('利空板块', [])
            if industry in bullish:
                policy_info = f"该行业({industry})受政策利好支持"
            elif industry in bearish:
                policy_info = f"该行业({industry})受政策利空影响"
        
        prompt = f"""你是一个量化交易策略专家。根据以下市场环境，选择最适合的策略：

市场环境:
- 趋势: {trend}
- 波动率: {vol}
- 行业: {industry}
- {policy_info}

可选策略:
{', '.join(ALL_STRATEGY_NAMES)}

规则:
- 上涨趋势: 优先趋势跟踪策略(MACD, MA, PSAR, ICHIMOKU)
- 下跌趋势: 优先防守策略(RSI, 布林带, 均值回归)
- 震荡市场: 优先区间策略(BB, RSI, KC)
- 高波动: 优先突破策略(BRK, VOLBRK)
- 低波动: 优先趋势策略(MA, MACD)

请推荐2-3个最适合当前环境的策略，按优先级排序。

输出格式:
策略1: 策略名
策略2: 策略名
策略3: 策略名

只输出策略名称，不要其他内容。"""
        
        # 3. 调用AI
        result = self.call_ai(prompt)
        
        # 4. 解析结果
        selected = []
        
        for line in result.split('\n'):
            line = line.strip()
            if ':' in line:
                strategy = line.split(':')[-1].strip()
                # 匹配策略名
                for s in ALL_STRATEGY_NAMES:
                    if s.upper() in strategy.upper() or strategy.upper() in s.upper():
                        if s not in selected:
                            selected.append(s)
                            break
        
        # 如果AI失败，使用规则
        if not selected:
            selected = self.rule_based_selection(env, industry)
        
        return selected[:3]  # 最多返回3个
    
    def rule_based_selection(self, env, industry: str) -> list:
        """基于规则的选择"""
        trend = env['trend']
        vol = env['volatility']
        
        # 趋势策略
        trend_strategies = ['MA5_10', 'MA10_20', 'MACD', 'PSAR']
        # 震荡策略
        range_strategies = ['BB', 'RSI', 'KC']
        # 动量策略
        momentum_strategies = ['MOM', 'BRK20', 'CCI']
        
        if trend == '上涨':
            return trend_strategies[:2]
        elif trend == '下跌':
            return ['BB', 'RSI'] + trend_strategies[:1]
        else:  # 震荡
            return range_strategies[:2] + momentum_strategies[:1]

# ============== 测试 ==============
if __name__ == '__main__':
    import pandas as pd
    import numpy as np
    
    # 模拟数据
    dates = pd.date_range('2025-01-01', periods=100)
    close = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({'close': close, 'high': close*1.02, 'low': close*0.98})
    df.index = dates
    
    selector = AIStrategySelector()
    
    print("="*50)
    print("AI策略选择测试")
    print("="*50)
    
    # 测试不同市场环境
    for industry in ['新能源', '银行', '白酒']:
        strategies = selector.select_strategy(df, industry)
        print(f"\n{industry}: {strategies}")
