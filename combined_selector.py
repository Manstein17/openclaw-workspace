"""
策略回测 + AI市场环境判断 综合选择器
- 每个策略进行回测获取历史收益
- AI分析当前市场环境
- 综合两者做买入决策
- 严格控制API调用（每天最多1次AI分析）
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

# API配置
MINIMAX_API_KEY = "sk-api-1AFALQluMHGe0SU5dl84QpbUXTLXjEOBZq-4mwjvCakyi-9NPvuTdCUMWJC6OmGnhVKirRC5grvnlOhlm-Ugm_YKCJnqLHLl8e0jYZXZsxtVDQm23PAOlEQ"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"

class CombinedStrategySelector:
    """综合策略选择器：回测 + AI"""
    
    CACHE_FILE = "/tmp/ai_market_cache.json"
    CACHE_DURATION = 4 * 60 * 60  # 4小时缓存
    
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        """加载缓存"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    # 检查是否过期
                    if datetime.now().timestamp() - data.get('timestamp', 0) < self.CACHE_DURATION:
                        print(f"   [缓存命中] 市场环境: {data.get('trend', 'N/A')}")
                        return data
            except:
                pass
        return {}
    
    def _save_cache(self, data: dict):
        """保存缓存"""
        data['timestamp'] = datetime.now().timestamp()
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def run_backtest(self, df: pd.DataFrame, strategy_signal_func) -> float:
        """
        简化的策略回测
        返回: 历史收益率 (%)
        """
        if df is None or len(df) < 30:
            return 0.0
        
        signals = []
        prices = df['close'].values
        
        # 生成信号序列
        for i in range(20, len(df)):
            signal = strategy_signal_func(df.iloc[:i+1])
            signals.append(signal)
        
        if not signals:
            return 0.0
        
        # 计算收益
        returns = []
        position = 0
        
        for i in range(len(signals)):
            if signals[i] == 1 and position == 0:  # 买入
                position = prices[i + 20]
            elif signals[i] == -1 and position > 0:  # 卖出
                ret = (prices[i + 20] - position) / position * 100
                returns.append(ret)
                position = 0
        
        # 持有收益
        if position > 0:
            ret = (prices[-1] - position) / position * 100
            returns.append(ret)
        
        if returns:
            return np.mean(returns)
        return 0.0
    
    def get_ai_market_analysis(self, df: pd.DataFrame = None) -> dict:
        """
        获取AI市场分析（带缓存）
        每天只调用一次API
        """
        # 检查缓存
        if self.cache and 'trend' in self.cache:
            return self.cache
        
        # 需要调用API
        print("   [AI] 分析市场环境...")
        
        # 基础分析
        trend = "震荡"
        volatility = "中等"
        
        if df is not None and len(df) >= 30:
            close = df['close']
            ma5 = close.rolling(5).mean()
            ma20 = close.rolling(20).mean()
            
            if ma5.iloc[-1] > ma20.iloc[-1] * 1.02:
                trend = "上涨"
            elif ma5.iloc[-1] < ma20.iloc[-1] * 0.98:
                trend = "下跌"
            
            vol = close.pct_change().std()
            volatility = "高" if vol > 0.03 else ("低" if vol < 0.015 else "中等")
        
        # 尝试调用AI获取更准确的分析
        try:
            import requests
            url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"
            headers = {"Authorization": f"Bearer {MINIMAX_API_KEY}", "Content-Type": "application/json"}
            
            prompt = f"""快速分析当前A股市场环境，只需回答以下格式（不超过50字）：

市场趋势(上涨/下跌/震荡): 
波动率(高/低/中等): 
建议策略类型(趋势/震荡/突破): 

只输出三行，不要其他内容。"""
            
            data = {"model": "MiniMax-M2.5", "messages": [{"role": "user", "content": prompt}]}
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result:
                    content = result['choices'][0]['message']['content']
                    # 简单解析
                    for line in content.split('\n'):
                        if '上涨' in line: trend = '上涨'
                        elif '下跌' in line: trend = '下跌'
                        elif '震荡' in line: trend = '震荡'
        except Exception as e:
            print(f"   [AI] API调用失败，使用基础分析: {e}")
        
        # 保存缓存
        result = {'trend': trend, 'volatility': volatility, 'timestamp': datetime.now().timestamp()}
        self._save_cache(result)
        print(f"   [AI] 市场分析完成: {trend}市, 波动率{volatility}")
        
        return result
    
    def select_strategies(self, market_env: dict) -> list:
        """
        根据市场环境选择适合的策略
        """
        trend = market_env.get('trend', '震荡')
        volatility = market_env.get('volatility', '中等')
        
        # 策略池
        trend_strats = ['MA5_10', 'MA10_20', 'MACD', 'PSAR', 'ICHIMOKU']
        range_strats = ['BB', 'RSI', 'KC', 'MR']
        momentum_strats = ['MOM', 'BRK20', 'CCI', 'STOCH']
        
        if trend == '上涨':
            return trend_strats[:3] + ['BB']
        elif trend == '下跌':
            return ['RSI', 'BB'] + trend_strats[:2]
        else:  # 震荡
            return range_strats[:2] + momentum_strats[:2]
    
    def combined_score(self, backtest_return: float, market_env: dict, 
                      ai_recommends: list, strategy_name: str) -> float:
        """
        综合评分 = 回测收益 + AI市场匹配
        """
        # 回测得分 (归一化到 -20 到 +20)
        backtest_score = max(-20, min(20, backtest_return))
        
        # AI匹配得分
        ai_score = 10 if strategy_name in ai_recommends else 0
        
        return backtest_score + ai_score


# ============== 测试 ==============
if __name__ == '__main__':
    # 测试
    selector = CombinedStrategySelector()
    
    # 模拟市场数据
    dates = pd.date_range('2025-01-01', periods=100)
    close = 100 + np.cumsum(np.random.randn(100))
    df = pd.DataFrame({'close': close, 'high': close*1.02, 'low': close*0.98}, index=dates)
    
    # 获取AI分析
    env = selector.get_ai_market_analysis(df)
    print(f"\n市场环境: {env}")
    
    # 获取推荐策略
    recs = selector.select_strategies(env)
    print(f"推荐策略: {recs}")
