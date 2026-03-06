#!/usr/bin/env python3
"""
资金流向模块
优先使用东财API获取真实资金流向
估算作为备选方案
"""
import requests
import os

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

class FundFlowEstimator:
    """资金流向获取 - 东财API优先"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({'User-Agent': 'Mozilla/5.0'})
    
    def get_eastmoney_fund_flow(self, symbol):
        """
        获取东财真实资金流向
        
        Returns:
            dict: {
                'main_flow': 主力净流入(万元),
                'large_flow': 大单净流入(万元),
                'medium_flow': 中单净流入(万元),
                'small_flow': 小单净流入(万元),
                'source': 'eastmoney'
            }
        """
        # 判断市场
        if symbol.startswith('6') or symbol.startswith('9'):
            secid = f'1.{symbol}'  # 上海
        else:
            secid = f'0.{symbol}'  # 深圳
        
        url = 'https://push2.eastmoney.com/api/qt/stock/get'
        params = {
            'fltt': 2,
            'fields': 'f43,f52,f53,f54,f55,f57,f58,f59,f60,f169,f170',
            'secid': secid
        }
        
        try:
            r = self.session.get(url, params=params, timeout=10)
            data = r.json()
            
            if data.get('data'):
                d = data['data']
                return {
                    'success': True,
                    'price': d.get('f43'),  # 最新价
                    'main_flow': d.get('f52', 0),  # 主力净流入(万元)
                    'large_flow': d.get('f55', 0),  # 大单净流入
                    'medium_flow': d.get('f54', 0),  # 中单净流入
                    'small_flow': d.get('f53', 0),  # 小单净流入
                    'turnover': d.get('f57', 0),  # 换手率
                    'amount': d.get('f58', 0),  # 成交额(万元)
                    'source': 'eastmoney'
                }
        except Exception as e:
            pass
        
        return {'success': False, 'source': 'eastmoney', 'error': str(e)}
    
    def get_tencent_quote(self, symbol):
        """获取腾讯实时行情"""
        if symbol.startswith('6') or symbol.startswith('9'):
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
                    'volume': int(parts[6]),
                    'amount': float(parts[7]),
                    'source': 'tencent'
                }
        except:
            pass
        return None
    
    def estimate_fund_flow(self, symbol):
        """
        估算资金流向 (东财失败时的备选)
        """
        quote = self.get_tencent_quote(symbol)
        
        if not quote:
            return {'main_flow': 0, 'score': 0, 'source': 'fail'}
        
        price = quote['price']
        volume = quote['volume']
        
        # 简单估算: 根据成交量估算
        # 假设成交量大时主力流入
        volume_level = min(volume / 100000, 2)
        
        # 估算
        flow = volume_level * 100  # 估算值
        
        # 评分: 基于成交量
        score = min(int(volume_level * 30), 60)
        
        return {
            'main_flow': flow,
            'score': score,
            'source': 'estimate'
        }
    
    def get_fund_flow(self, symbol):
        """
        获取资金流向 - 优先东财，备选估算
        
        Returns:
            dict: {
                'main_flow': 主力净流入(万元),
                'score': 评分(-100到100),
                'source': 'eastmoney' or 'estimate'
            }
        """
        # 先尝试东财API
        result = self.get_eastmoney_fund_flow(symbol)
        
        if result.get('success'):
            main_flow = result.get('main_flow', 0)
            
            # 转换为评分
            # 主力流入>1000万 -> +60分
            # 主力流入>500万 -> +40分
            # 主力流入>100万 -> +20分
            # 主力流入<0 -> -20分
            
            if main_flow > 1000:
                score = 60
            elif main_flow > 500:
                score = 40
            elif main_flow > 100:
                score = 20
            elif main_flow > 0:
                score = 10
            else:
                score = -20
            
            return {
                'main_flow': main_flow,
                'score': score,
                'source': 'eastmoney',
                'large_flow': result.get('large_flow', 0),
                'turnover': result.get('turnover', 0)
            }
        
        # 东财失败，使用估算
        return self.estimate_fund_flow(symbol)


# 测试
if __name__ == '__main__':
    print("=== 资金流向测试 ===\n")
    
    estimator = FundFlowEstimator()
    
    for symbol in ['300861', '688613', '300715']:
        print(f"📊 {symbol}:")
        result = estimator.get_fund_flow(symbol)
        
        if result.get('success') or result.get('source') == 'eastmoney':
            print(f"   主力净流入: {result.get('main_flow', 0):+.2f}万元")
            print(f"   评分: {result.get('score', 0)}")
            print(f"   数据源: {result.get('source')}")
        else:
            print(f"   估算: {result.get('main_flow'):+.0f}万元")
            print(f"   评分: {result.get('score')}")
            print(f"   数据源: {result.get('source')}")
        print()
