#!/usr/bin/env python3
"""
资金流向估算模块
基于成交量和价格变动估算资金流向
当东财API不可用时作为备选方案
"""
import requests
import os
import time
from datetime import datetime

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

class FundFlowEstimator:
    """基于腾讯数据估算资金流向"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.cache = {}
    
    def get_quote(self, symbol):
        """获取实时行情"""
        # 判断市场
        if symbol.startswith('6'):
            code = f'sh{symbol}'
        else:
            code = f'sz{symbol}'
        
        url = f'https://qt.gtimg.cn/q={code}'
        
        try:
            r = self.session.get(url, timeout=5)
            data = r.text
            
            if data and 'v_' in data:
                parts = data.split('=')[1].split('~')
                
                return {
                    'price': float(parts[3]),
                    'high': float(parts[4]),
                    'low': float(parts[5]),
                    'volume': int(parts[6]),  # 手
                    'amount': float(parts[7]),  # 万
                    'open': float(parts[10]) if parts[10] else None,
                    'pct': float(parts[3]) - float(parts[2]) if len(parts) > 3 else 0
                }
        except:
            pass
        
        return None
    
    def estimate_fund_flow(self, symbol):
        """
        估算资金流向
        基于:
        1. 涨跌幅方向
        2. 成交量变化
        3. 价格相对于开盘的位置
        """
        quote = self.get_quote(symbol)
        
        if not quote:
            return {'flow': 0, 'score': 0, 'source': 'fail'}
        
        # 简单估算逻辑
        # 1. 如果价格高于开盘，且成交量大 → 资金流入
        # 2. 如果价格低于开盘，且成交量大 → 资金流出
        
        price = quote['price']
        volume = quote['volume']
        open_price = quote.get('open', price)
        
        # 涨跌幅方向
        direction = 1 if price >= open_price else -1
        
        # 成交量等级 (假设日均10万手为中等)
        volume_level = min(volume / 100000, 3)  # 最大3倍
        
        # 估算资金流向 (单位: 万元)
        estimated_flow = direction * volume * (price / 10) * 0.5  # 简化计算
        
        # 评分
        if estimated_flow > 5000:  # 5000万
            score = 20
        elif estimated_flow > 1000:  # 1000万
            score = 10
        elif estimated_flow > 0:
            score = 5
        elif estimated_flow > -1000:
            score = 0
        else:
            score = -10
        
        return {
            'flow': estimated_flow,
            'score': score,
            'price': price,
            'volume': volume,
            'direction': '流入' if direction > 0 else '流出',
            'source': 'estimate'
        }
    
    def get_stock_fund_flow(self, symbol, name=None):
        """获取股票资金流向 (优先使用东财，失败则估算)"""
        # 先尝试估算
        result = self.estimate_fund_flow(symbol)
        
        # 缓存
        self.cache[symbol] = {
            **result,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        return self.cache[symbol]
    
    def get_fund_flow_score(self, symbol, name=None):
        """获取资金流向评分"""
        result = self.get_stock_fund_flow(symbol, name)
        return result.get('score', 0)


# 测试
if __name__ == "__main__":
    estimator = FundFlowEstimator()
    
    print("=== 资金流向估算测试 ===\n")
    
    stocks = ['300861', '300719', '300678', '300875', '000428']
    
    for s in stocks:
        result = estimator.get_stock_fund_flow(s)
        flow = result.get('flow', 0)
        score = result.get('score', 0)
        
        print(f"{s}: 估算{flow/10000:.1f}万, 评分:{score}")
