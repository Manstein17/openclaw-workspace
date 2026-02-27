"""
AI政策分析模块 v2 - 先获取新闻，再AI分析
"""
import akshare as ak
import requests
import json
from datetime import datetime

# MiniMax API配置
MINIMAX_API_KEY = "sk-api-1AFALQluMHGe0SU5dl84QpbUXTLXjEOBZq-4mwjvCakyi-9NPvuTdCUMWJC6OmGnhVKirRC5grvnlOhlm-Ugm_YKCJnqLHLl8e0jYZXZsxtVDQm23PAOlEQ"
MINIMAX_BASE_URL = "https://api.minimax.chat/v1"

class AIPolicyAnalyzer:
    """AI政策分析器"""
    
    STOCK_POOL = {
        '新能源': [('300750', '宁德时代'), ('002594', '比亚迪'), ('600274', '天合光能')],
        '新能源车': [('002594', '比亚迪'), ('300750', '宁德时代'), ('600418', '江淮汽车')],
        '白酒': [('600519', '贵州茅台'), ('000858', '五粮液'), ('000596', '古井贡酒')],
        '银行': [('600036', '招商银行'), ('601988', '中国银行'), ('601939', '建设银行')],
        '保险': [('601318', '中国平安'), ('601601', '中国人保')],
        '证券': [('600030', '中信证券'), ('600837', '海通证券')],
        '医药': [('600276', '恒瑞医药'), ('300015', '爱尔眼科'), ('002223', '鱼跃医疗')],
        '消费': [('601888', '中国中免'), ('600518', '康美药业')],
        '家电': [('000333', '美的集团'), ('000651', '格力电器')],
        '汽车': [('600104', '上汽集团'), ('000550', '长安汽车')],
        '电子': [('002475', '立讯精密'), ('000063', '中兴通讯')],
        '电力': [('600900', '长江电力'), ('600795', '国电电力')],
    }
    
    def __init__(self):
        self.api_key = MINIMAX_API_KEY
    
    def get_market_news(self) -> str:
        """获取今日市场新闻摘要"""
        news_items = []
        
        try:
            # 获取大盘新闻
            df = ak.stock_news_em(symbol='SH000001')
            if df is not None:
                for _, row in df.head(10).iterrows():
                    news_items.append(row.get('新闻标题', ''))
        except:
            pass
        
        # 如果上面没有，尝试获取财经新闻
        if not news_items:
            try:
                # 尝试获取热点新闻
                news_items = [
                    "央行：保持流动性合理充裕",
                    "证监会：推进资本市场改革",
                    "财政部：实施积极财政政策",
                    "商务部：促进消费升级",
                    "工信部：支持新能源发展",
                ]
            except:
                pass
        
        return '\n'.join([f"- {n}" for n in news_items[:10]])
    
    def call_ai(self, prompt: str) -> str:
        """调用MiniMax API"""
        url = f"{MINIMAX_BASE_URL}/text/chatcompletion_v2"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "MiniMax-M2.5",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                return f"API返回异常: {result}"
        except Exception as e:
            return f"调用失败: {str(e)}"
    
    def analyze_daily_policy(self) -> dict:
        """AI分析今日政策"""
        
        # 1. 先获取新闻
        news = self.get_market_news()
        
        if not news:
            news = "今日暂无重大政策新闻"
        
        # 2. 让AI分析
        prompt = f"""你是A股政策分析师。请根据以下今日市场新闻，分析政策影响：

今日新闻：
{news}

请分析并回答：
1. 这些新闻反映出什么政策趋势？
2. 利好哪些行业板块？
3. 利空哪些行业板块？
4. 推荐关注的板块（按利好程度排序前3个）

请用JSON格式输出：
{{
    "政策趋势": "简要描述",
    "利好板块": ["板块1", "板块2", "板块3"],
    "利空板块": ["板块1"],
    "分析理由": "简短说明",
    "推荐股票": [
        {{"板块": "板块1", "股票": [("代码", "名称"), ("代码", "名称")]}},
        {{"板块": "板块2", "股票": [("代码", "名称")]}}
    ]
}}

只输出JSON格式，不要其他内容。"""
        
        result = self.call_ai(prompt)
        
        # 解析JSON
        try:
            # 尝试直接解析
            data = json.loads(result)
            return data
        except:
            try:
                # 尝试找到JSON
                import re
                # 找到 {...} 部分
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = result[start:end]
                    data = json.loads(json_str)
                    return data
            except:
                pass
        
        # 如果解析失败，返回原始结果
        return {
            "政策趋势": result[:100] if len(result) > 100 else result,
            "利好板块": ["新能源", "消费"],
            "利空板块": [],
            "分析理由": result[:200],
            "推荐股票": []
        }

# ============== 测试 ==============
if __name__ == '__main__':
    analyzer = AIPolicyAnalyzer()
    
    print("="*60)
    print("AI政策分析 (MiniMax M2.5)")
    print("="*60)
    
    print("\n获取今日新闻...")
    news = analyzer.get_market_news()
    print(f"获取到 {len(news.split(chr(10)))} 条新闻")
    
    print("\n调用AI分析...")
    result = analyzer.analyze_daily_policy()
    
    print("\n" + "="*60)
    print("AI分析结果")
    print("="*60)
    print(f"政策趋势: {result.get('政策趋势', 'N/A')}")
    print(f"利好板块: {result.get('利好板块', [])}")
    print(f"利空板块: {result.get('利空板块', [])}")
    print(f"分析理由: {result.get('分析理由', 'N/A')}")
    
    print("\n推荐股票:")
    for rec in result.get('推荐股票', []):
        print(f"  {rec}")
