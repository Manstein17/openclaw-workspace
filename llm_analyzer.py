#!/usr/bin/env python3
"""
LLM股票分析器
将传统分析数据发送给LLM进行深度分析
"""
import os
import json
import requests

# 读取API Key
API_KEY_FILE = os.path.expanduser('~/.openclaw/.credentials/minimax_api_key.txt')
if os.path.exists(API_KEY_FILE):
    with open(API_KEY_FILE) as f:
        MINIMAX_API_KEY = f.read().strip()
else:
    MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')

MINIMAX_BASE_URL = 'https://api.minimax.chat/v1/text/chatcompletion_v2'

class LLMStockAnalyzer:
    """LLM股票分析器"""
    
    def __init__(self):
        self.api_key = MINIMAX_API_KEY
        self.base_url = MINIMAX_BASE_URL
        self.model = 'MiniMax-M2.1'
    
    def analyze(self, stock_data: dict) -> dict:
        """
        分析单只股票
        """
        prompt = self._build_single_prompt(stock_data)
        
        try:
            response = self._call_llm(prompt)
            return {
                'success': True,
                'analysis': response,
                'recommendation': '需要人工判断'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_candidates(self, candidates: list) -> dict:
        """
        分析候选股票列表，选出最优
        """
        prompt = self._build_candidates_prompt(candidates)
        
        try:
            response = self._call_llm(prompt)
            return {
                'success': True,
                'analysis': response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_single_prompt(self, data: dict) -> str:
        """构建单只股票分析提示词"""
        
        prompt = f"""你是一个专业的A股量化分析师。请根据以下传统分析数据，给出投资建议。

## 股票信息
- 股票代码: {data.get('symbol', 'N/A')}
- 股票名称: {data.get('name', 'N/A')}
- 当前价格: ¥{data.get('current_price', 'N/A')}
- 所属行业: {data.get('industry', 'N/A')}

## 传统分析数据
- 综合评分: {data.get('score', 0)}分 (满分120+)
- 触发策略: {', '.join(data.get('strategies', []))}
- 策略胜率: {data.get('win_rate', 0):.1%}
- 主力资金: {data.get('fund_flow', 0):+.0f}万元

## 请给出分析

请直接给出买入/卖出/持有建议和理由。
"""
        return prompt
    
    def _build_candidates_prompt(self, candidates: list) -> str:
        """构建候选股票分析提示词"""
        
        prompt = """你是一个专业的A股量化分析师。请根据以下传统量化分析数据，从候选股票中选择最优的进行投资。

## 候选股票
"""
        
        for i, stock in enumerate(candidates[:5], 1):
            prompt += f"""
### {i}. {stock.get('symbol')} {stock.get('name')}
- 综合评分: {stock.get('score', 0)}分
- 所属行业: {stock.get('industry', 'N/A')}
- 触发策略: {', '.join(stock.get('strategies', []))}
- 策略胜率: {stock.get('win_rate', 0):.1%}
- 主力资金: {stock.get('fund_flow', 0):+.0f}万元
"""
        
        prompt += """
## 请选出最优的3只股票，并给出理由。

格式:
1. [股票代码] - 评分X分 - 理由
2. [股票代码] - 评分X分 - 理由
3. [股票代码] - 评分X分 - 理由
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': '你是一个专业的A股量化分析师。'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            raise Exception(f"API错误: {response.status_code} - {response.text[:100]}")


# 测试

    def analyze_policy(self, policy_summary: str) -> dict:
        """分析政策影响"""
        if not policy_summary:
            return {'success': False, 'error': 'No summary'}
        
        prompt = f"""你是一个专业的A股政策分析师。请根据以下政策新闻摘要，分析对A股市场的影响。

## 政策摘要
{policy_summary}

## 请分析
1. 哪些行业受益(利好)?
2. 哪些行业受损(利空)?
3. 整体市场情绪(利好/利空/中性)?
4. 推荐的行业板块?

请给出简洁的分析。
"""
        
        try:
            response = self._call_llm(prompt)
            return {'success': True, 'analysis': response}
        except Exception as e:
            return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    print("=== LLM分析测试 ===\n")
    
    analyzer = LLMStockAnalyzer()
    
    # 测试单只股票
    test_data = {
        'symbol': '688613',
        'name': '某科技',
        'current_price': 24.90,
        'industry': '半导体',
        'score': 89,
        'strategies': ['MA5_10', 'RSI', 'MACD'],
        'win_rate': 0.55,
        'fund_flow': 1000
    }
    
    print("📊 分析单只股票...")
    result = analyzer.analyze(test_data)
    
    if result.get('success'):
        print(f"\n✅ 分析结果:\n{result['analysis']}")

    def analyze_policy(self, policy_summary: str) -> dict:
        """分析政策影响"""
        if not policy_summary:
            return {'success': False, 'error': 'No summary'}
        
        prompt = f"""你是一个专业的A股政策分析师。请根据以下政策新闻摘要，分析对A股市场的影响。

## 政策摘要
{policy_summary}

## 请分析
1. 哪些行业受益(利好)?
2. 哪些行业受损(利空)?
3. 整体市场情绪(利好/利空/中性)?
4. 推荐的行业板块?

请给出简洁的分析。
"""
        
        try:
            response = self.session.post(
                self.base_url,
                headers=self.headers,
                json={
                    'model': self.model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'temperature': 0.7
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result['choices'][0]['message']['content']
                return {'success': True, 'analysis': analysis}
            else:
                return {'success': False, 'error': f'Status {response.status_code}'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}

if __name__ == '__main__':
    # 测试
    analyzer = LLMStockAnalyzer()
    test_data = {'symbol': '600000', 'name': '测试', 'score': 75}
    print("📊 分析单只股票...")
    result = analyzer.analyze(test_data)
    
    if result.get('success'):
        print(f"\n✅ 分析结果:\n{result['analysis']}")
    else:
        print(f"❌ 错误: {result.get('error')}")
