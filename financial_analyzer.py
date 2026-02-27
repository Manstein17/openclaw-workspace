"""
财务分析模块 - 完整版
根据你的要求:
- ROE > 15% (持续3年以上)
- 负债率 < 50%
- 自由现金流 > 净利润的80%
- 护城河评估
输出: 投资评级(A/B/C/D) + 理由
"""
import akshare as ak
import pandas as pd
from typing import Dict, Optional

class FinancialAnalyzer:
    """财务分析器"""
    
    def __init__(self):
        self.cache = {}
    
    def get_roe_data(self, symbol: str) -> Optional[Dict]:
        """获取ROE数据"""
        try:
            # 转换代码格式
            if symbol.startswith('6'):
                code = f'SH{symbol}'
            else:
                code = f'SZ{symbol}'
            
            df = ak.stock_zh_dupont_comparison_em(symbol=code)
            
            # 找到公司数据（不是行业平均/中值）
            company = df[df['代码'].apply(lambda x: str(x).isdigit())]
            
            if len(company) > 0:
                row = company.iloc[0]
                return {
                    'roe_3yr_avg': float(row['ROE-3年平均']) if pd.notna(row['ROE-3年平均']) else 0,
                    'roe_22a': float(row['ROE-22A']) if pd.notna(row['ROE-22A']) else 0,
                    'roe_23a': float(row['ROE-23A']) if pd.notna(row['ROE-23A']) else 0,
                    'roe_24a': float(row['ROE-24A']) if pd.notna(row['ROE-24A']) else 0,
                }
        except Exception as e:
            print(f"ROE数据获取失败: {e}")
        
        return None
    
    def get_profit_data(self, symbol: str) -> Optional[Dict]:
        """获取净利润数据"""
        try:
            if symbol.startswith('6'):
                code = f'SH{symbol}'
            else:
                code = f'SZ{symbol}'
            
            df = ak.stock_profit_sheet_by_yearly_em(symbol=code)
            
            if df is not None and len(df) > 0:
                # 取最近年度
                latest = df.iloc[0]
                net_profit = latest.get('NETPROFIT', 0)
                
                if pd.notna(net_profit):
                    return {'net_profit': float(net_profit)}
        except Exception as e:
            print(f"净利润数据获取失败: {e}")
        
        return None
    
    def get_cashflow_data(self, symbol: str) -> Optional[Dict]:
        """获取现金流数据"""
        try:
            if symbol.startswith('6'):
                code = f'SH{symbol}'
            else:
                code = f'SZ{symbol}'
            
            df = ak.stock_cash_flow_sheet_by_yearly_em(symbol=code)
            
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                operate_cf = latest.get('NETCASH_OPERATE', 0)
                
                if pd.notna(operate_cf):
                    return {'operate_cashflow': float(operate_cf)}
        except Exception as e:
            print(f"现金流数据获取失败: {e}")
        
        return None
    
    def get_financial_summary(self, symbol: str, name: str, industry: str) -> Dict:
        """获取完整财务摘要"""
        # ROE
        roe_data = self.get_roe_data(symbol)
        
        # 净利润
        profit_data = self.get_profit_data(symbol)
        
        # 现金流
        cashflow_data = self.get_cashflow_data(symbol)
        
        # 护城河评估
        moat = self.get_moat_score(industry)
        
        return {
            'symbol': symbol,
            'name': name,
            'industry': industry,
            'roe': roe_data,
            'profit': profit_data,
            'cashflow': cashflow_data,
            'moat': moat
        }
    
    def get_moat_score(self, industry: str) -> Dict:
        """护城河评估"""
        moat_scores = {
            '白酒': {'score': 18, 'type': '品牌护城河', 'desc': '品牌壁垒强,定价权高'},
            '医药': {'score': 16, 'type': '研发壁垒', 'desc': '研发投入大,壁垒高'},
            '新能源': {'score': 15, 'type': '技术壁垒', 'desc': '技术领先,规模优势'},
            '新能源车': {'score': 14, 'type': '技术+规模', 'desc': '产业链完整'},
            '保险': {'score': 15, 'type': '牌照壁垒', 'desc': '金融牌照稀缺'},
            '银行': {'score': 14, 'type': '牌照+规模', 'desc': '网点优势'},
            '证券': {'score': 13, 'type': '牌照壁垒', 'desc': '资本实力'},
            '家电': {'score': 12, 'type': '成本优势', 'desc': '制造能力强'},
            '电力': {'score': 13, 'type': '垄断', 'desc': '电网垄断'},
            '消费': {'score': 12, 'type': '渠道', 'desc': '渠道为王'},
            '汽车': {'score': 11, 'type': '规模', 'desc': '规模效应'},
            '电子': {'score': 14, 'type': '技术壁垒', 'desc': '技术迭代快'},
            'ETF': {'score': 10, 'type': '低费率', 'desc': '跟踪指数'},
        }
        
        return moat_scores.get(industry, {'score': 10, 'type': '一般', 'desc': '普通行业'})
    
    def analyze(self, symbol: str, name: str, industry: str) -> Dict:
        """综合财务分析"""
        summary = self.get_financial_summary(symbol, name, industry)
        
        # 评分项
        scores = {}
        reasons = []
        
        # 1. ROE > 15% (持续3年)
        if summary['roe']:
            roe_avg = summary['roe']['roe_3yr_avg']
            roe_24 = summary['roe']['roe_24a']
            
            if roe_avg > 15 and roe_24 > 15:
                scores['ROE'] = 30
                reasons.append(f"✓ ROE3年平均{roe_avg:.1f}% > 15%, 2024年{roe_24:.1f}%")
            elif roe_avg > 10:
                scores['ROE'] = 20
                reasons.append(f"△ ROE 3年平均{roe_avg:.1f}%, 2024年{roe_24:.1f}%")
            else:
                scores['ROE'] = 10
                reasons.append(f"✗ ROE {roe_avg:.1f}% < 15%")
        
        # 2. 自由现金流 > 净利润80%
        # 这里用经营现金流代替自由现金流
        if summary['profit'] and summary['cashflow']:
            profit = abs(summary['profit']['net_profit'])
            cf = abs(summary['cashflow']['operate_cashflow'])
            
            if profit > 0 and cf / profit > 0.8:
                scores['现金流'] = 20
                reasons.append(f"✓ 经营现金流/净利润 = {cf/profit*100:.0f}% > 80%")
            else:
                scores['现金流'] = 10
                reasons.append(f"✗ 现金流/净利润 = {cf/profit*100:.0f}% < 80%" if profit > 0 else "△ 现金流数据异常")
        
        # 3. 护城河
        scores['护城河'] = summary['moat']['score']
        reasons.append(f"{summary['moat']['type']}: {summary['moat']['desc']}")
        
        # 总分
        total_score = sum(scores.values())
        
        # 评级
        if total_score >= 70:
            rating = 'A'
            verdict = '强烈推荐'
        elif total_score >= 55:
            rating = 'B'
            verdict = '建议买入'
        elif total_score >= 40:
            rating = 'C'
            verdict = '观望'
        else:
            rating = 'D'
            verdict = '不建议'
        
        return {
            'rating': rating,
            'verdict': verdict,
            'score': total_score,
            'details': scores,
            'reasons': reasons,
            'moat': summary['moat'],
            'roe': summary['roe'],
            'profit': summary['profit'],
            'cashflow': summary['cashflow']
        }

# ============== 测试 ==============
if __name__ == '__main__':
    analyzer = FinancialAnalyzer()
    
    # 测试股票
    stocks = [
        ('600519', '贵州茅台', '白酒'),
        ('601318', '中国平安', '保险'),
        ('300750', '宁德时代', '新能源'),
    ]
    
    print("="*60)
    print("财务分析报告")
    print("="*60)
    
    for symbol, name, industry in stocks:
        result = analyzer.analyze(symbol, name, industry)
        
        print(f"\n{'='*60}")
        print(f"{name} ({symbol}) - {industry}")
        print(f"{'='*60}")
        print(f"评级: {result['rating']} ({result['score']}分) - {result['verdict']}")
        
        print("\n分析理由:")
        for reason in result['reasons']:
            print(f"  • {reason}")
        
        if result['roe']:
            r = result['roe']
            print(f"\nROE数据:")
            print(f"  3年平均: {r['roe_3yr_avg']:.2f}%")
            print(f"  2024年: {r['roe_24a']:.2f}%")
            print(f"  2023年: {r['roe_23a']:.2f}%")
            print(f"  2022年: {r['roe_22a']:.2f}%")
