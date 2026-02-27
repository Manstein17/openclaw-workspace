"""
政策分析模块 v2 - 简化版
基于当前宏观环境和历史政策倾向进行分析
"""
import akshare as ak
import pandas as pd
from datetime import datetime

class PolicyAnalyzer:
    """政策分析器"""
    
    # 当前宏观政策环境 (2025-2026)
    CURRENT_POLICIES = {
        # 持续利好
        '白酒': {'score': 1, 'status': '利好', 'reason': '消费复苏政策支持'},
        '新能源': {'score': 2, 'status': '利好', 'reason': '双碳目标+补贴政策'},
        '新能源车': {'score': 2, 'status': '利好', 'reason': '购置税减免延续'},
        '电力': {'score': 1, 'status': '利好', 'reason': '能源保供+新基建'},
        '银行': {'score': 1, 'status': '利好', 'reason': '化债政策支持'},
        
        # 政策不确定
        '保险': {'score': 0, 'status': '中性', 'reason': '利率环境变化'},
        '证券': {'score': 0, 'status': '中性', 'reason': '市场行情依赖'},
        '医药': {'score': -1, 'status': '利空', 'reason': '集采常态化'},
        
        # 政策压制
        '房地产': {'score': -2, 'status': '利空', 'reason': '房住不炒基调'},
        '家电': {'score': 0, 'status': '中性', 'reason': '以旧换新政策'},
        '消费': {'score': 1, 'status': '利好', 'reason': '扩内需政策'},
        '汽车': {'score': 1, 'status': '利好', 'reason': '以旧换新补贴'},
        '电子': {'score': 1, 'status': '利好', 'reason': '科技创新支持'},
    }
    
    def __init__(self):
        pass
    
    def get_policy(self, industry: str) -> dict:
        """获取行业政策评级"""
        return self.CURRENT_POLICIES.get(industry, {'score': 0, 'status': '中性', 'reason': '无重大政策'})
    
    def analyze(self, industry: str) -> dict:
        """分析行业政策"""
        policy = self.get_policy(industry)
        
        score = policy['score']
        
        if score >= 2:
            rating = 'A'
            verdict = '政策强烈利好'
        elif score >= 1:
            rating = 'B'
            verdict = '政策利好'
        elif score <= -2:
            rating = 'D'
            verdict = '政策利空'
        elif score <= -1:
            rating = 'C'
            verdict = '政策利空'
        else:
            rating = 'C'
            verdict = '政策中性'
        
        return {
            'rating': rating,
            'verdict': verdict,
            'score': score,
            'status': policy['status'],
            'reason': policy['reason'],
            'industry': industry
        }
    
    def get_macro_data(self) -> dict:
        """获取宏观数据辅助判断"""
        data = {}
        
        try:
            # CPI
            df = ak.macro_china_cpi()
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                cpi = float(latest.get('全国-同比增长', 0))
                data['cpi'] = cpi
                
                # 判断通胀环境
                if cpi > 3:
                    data['inflation'] = '高通胀'
                    data['policy_expect'] = '收紧'
                elif cpi > 0:
                    data['inflation'] = '温和通胀'
                    data['policy_expect'] = '稳健'
                else:
                    data['inflation'] = '通缩'
                    data['policy_expect'] = '宽松'
        except:
            pass
        
        return data

# ============== 测试 ==============
if __name__ == '__main__':
    analyzer = PolicyAnalyzer()
    
    print("="*60)
    print("政策分析")
    print("="*60)
    
    # 宏观数据
    macro = analyzer.get_macro_data()
    if macro:
        print(f"\n宏观环境:")
        print(f"  CPI: {macro.get('cpi', 'N/A')}%")
        print(f"  通胀: {macro.get('inflation', 'N/A')}")
        print(f"  政策预期: {macro.get('policy_expect', 'N/A')}")
    
    # 行业政策
    print("\n行业政策评级:")
    industries = ['白酒', '新能源', '新能源车', '银行', '保险', '证券', 
                 '医药', '房地产', '家电', '消费', '汽车', '电子']
    
    results = []
    for ind in industries:
        result = analyzer.analyze(ind)
        results.append(result)
    
    # 按评分排序
    results.sort(key=lambda x: x['score'], reverse=True)
    
    for r in results:
        print(f"  {r['industry']:8s} | {r['rating']}级 | {r['verdict']} | {r['reason']}")
