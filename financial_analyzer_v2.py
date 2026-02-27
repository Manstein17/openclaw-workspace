"""
财务分析模块 v2 - 完整版
整合到主系统
"""
import akshare as ak
import pandas as pd
from typing import Dict, Optional

class FinancialAnalyzer:
    """财务分析器"""
    
    # 行业平均负债率（作为参考）
    INDUSTRY_DEBT_RATIOS = {
        '白酒': 35,    # 轻资产，负债率低
        '医药': 40,    # 研发投入大，负债适中
        '新能源': 55,  # 重资产，负债较高
        '新能源车': 60,
        '保险': 75,    # 保险公司特殊商业模式
        '银行': 92,    # 银行高负债是正常的
        '家电': 65,
        '电力': 70,
        '消费': 45,
        '汽车': 65,
        '电子': 55,
        '证券': 70,
        'ETF': 5,
    }
    
    def __init__(self):
        self.cache = {}
    
    def get_roe_data(self, symbol: str) -> Optional[Dict]:
        """获取ROE数据"""
        try:
            code = f'SH{symbol}' if symbol.startswith('6') else f'SZ{symbol}'
            df = ak.stock_zh_dupont_comparison_em(symbol=code)
            company = df[df['代码'].apply(lambda x: str(x).isdigit())]
            
            if len(company) > 0:
                row = company.iloc[0]
                return {
                    'roe_3yr_avg': float(row['ROE-3年平均']) if pd.notna(row['ROE-3年平均']) else 0,
                    'roe_22a': float(row['ROE-22A']) if pd.notna(row['ROE-22A']) else 0,
                    'roe_23a': float(row['ROE-23A']) if pd.notna(row['ROE-23A']) else 0,
                    'roe_24a': float(row['ROE-24A']) if pd.notna(row['ROE-24A']) else 0,
                }
        except:
            pass
        return None
    
    def get_profit_data(self, symbol: str) -> Optional[Dict]:
        """获取净利润"""
        try:
            code = f'SH{symbol}' if symbol.startswith('6') else f'SZ{symbol}'
            df = ak.stock_profit_sheet_by_yearly_em(symbol=code)
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                net_profit = latest.get('NETPROFIT', 0)
                if pd.notna(net_profit):
                    return {'net_profit': float(net_profit)}
        except:
            pass
        return None
    
    def get_cashflow_data(self, symbol: str) -> Optional[Dict]:
        """获取现金流"""
        try:
            code = f'SH{symbol}' if symbol.startswith('6') else f'SZ{symbol}'
            df = ak.stock_cash_flow_sheet_by_yearly_em(symbol=code)
            if df is not None and len(df) > 0:
                latest = df.iloc[0]
                operate_cf = latest.get('NETCASH_OPERATE', 0)
                if pd.notna(operate_cf):
                    return {'operate_cashflow': float(operate_cf)}
        except:
            pass
        return None
    
    def get_moat_info(self, industry: str) -> Dict:
        """护城河信息"""
        moat_data = {
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
        return moat_data.get(industry, {'score': 10, 'type': '一般', 'desc': '普通行业'})
    
    def analyze(self, symbol: str, name: str, industry: str) -> Dict:
        """综合财务分析"""
        # 数据获取
        roe_data = self.get_roe_data(symbol)
        profit_data = self.get_profit_data(symbol)
        cashflow_data = self.get_cashflow_data(symbol)
        moat = self.get_moat_info(industry)
        
        # 评分
        scores = {}
        reasons = []
        
        # 1. ROE > 15% (持续3年) - 25分
        if roe_data:
            avg = roe_data['roe_3yr_avg']
            current = roe_data['roe_24a']
            
            if avg > 15 and current > 15:
                scores['ROE'] = 25
                reasons.append(f"✓ ROE 3年均{avg:.1f}% > 15%, 2024年{current:.1f}%")
            elif avg > 10:
                scores['ROE'] = 15
                reasons.append(f"△ ROE 3年均{avg:.1f}%, 2024年{current:.1f}%")
            else:
                scores['ROE'] = 5
                reasons.append(f"✗ ROE {avg:.1f}% < 15%")
        
        # 2. 负债率 < 50% - 20分
        # 使用行业平均估算
        industry_debt = self.INDUSTRY_DEBT_RATIOS.get(industry, 50)
        
        # 白酒、医药等轻资产行业负债率通常较低
        # 银行、保险高负债是商业模式决定的
        if industry in ['银行', '保险', '证券']:
            # 金融行业特殊看待
            scores['负债率'] = 15
            reasons.append(f"△ 金融行业(负债{industry_debt}%为正常)")
        elif industry_debt < 50:
            scores['负债率'] = 20
            reasons.append(f"✓ 行业负债率{industry_debt}% < 50%")
        else:
            scores['负债率'] = 10
            reasons.append(f"△ 行业负债率{industry_debt}%")
        
        # 3. 现金流 > 净利润80% - 20分
        if profit_data and cashflow_data:
            profit = abs(profit_data['net_profit'])
            cf = abs(cashflow_data['operate_cashflow'])
            
            if profit > 0 and cf / profit > 0.8:
                scores['现金流'] = 20
                reasons.append(f"✓ 现金流/净利润={cf/profit*100:.0f}% > 80%")
            else:
                scores['现金流'] = 10
                if profit > 0:
                    reasons.append(f"✗ 现金流/净利润={cf/profit*100:.0f}%")
                else:
                    scores['现金流'] = 5
                    reasons.append("△ 净利润为负")
        else:
            scores['现金流'] = 10
            reasons.append("△ 现金流数据获取失败")
        
        # 4. 护城河 - 15分
        scores['护城河'] = moat['score']
        reasons.append(f"护城河: {moat['type']}-{moat['desc']}")
        
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
            'roe': roe_data,
            'moat': moat,
            'industry_debt': industry_debt
        }

# ============== 测试 ==============
if __name__ == '__main__':
    analyzer = FinancialAnalyzer()
    
    stocks = [
        ('600519', '贵州茅台', '白酒'),
        ('601318', '中国平安', '保险'),
        ('300750', '宁德时代', '新能源'),
    ]
    
    for symbol, name, industry in stocks:
        result = analyzer.analyze(symbol, name, industry)
        
        print(f"\n{'='*50}")
        print(f"{name} ({symbol})")
        print(f"评级: {result['rating']} ({result['score']}分) - {result['verdict']}")
        print(f"{'='*50}")
        
        for reason in result['reasons']:
            print(f"  • {reason}")
        
        if result['roe']:
            r = result['roe']
            print(f"\nROE: 3年均={r['roe_3yr_avg']:.1f}%, 2024={r['roe_24a']:.1f}%")
