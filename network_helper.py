#!/usr/bin/env python3
"""
网络工具 - 解决VPN代理问题
用于在中国金融API和VPN之间切换
"""
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class NetworkHelper:
    """网络助手 - 处理代理问题"""
    
    def __init__(self):
        self.session = None
        self._init_session()
    
    def _init_session(self):
        """初始化session - 禁用代理"""
        self.session = requests.Session()
        
        # 禁用所有代理 - 关键步骤
        self.session.trust_env = False
        
        # 设置重试
        adapter = HTTPAdapter(
            max_retries=Retry(total=2, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 设置UA
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def get_eastmoney(self, symbol: str) -> dict:
        """
        获取东财实时数据
        
        Args:
            symbol: 股票代码 (如 300861)
            
        Returns:
            股票数据字典
        """
        # 判断市场
        if symbol.startswith('6') or symbol.startswith('9'):
            secid = f'1.{symbol}'  # 上海
        else:
            secid = f'0.{symbol}'  # 深圳
        
        url = f'https://push2.eastmoney.com/api/qt/stock/get'
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
                    'main_flow': d.get('f52'),  # 主力净流入
                    'large_flow': d.get('f55'),  # 大单净流入
                    'medium_flow': d.get('f54'),  # 中单净流入
                    'small_flow': d.get('f53'),  # 小单净流入
                    'turnover': d.get('f57'),  # 换手率
                    'amount': d.get('f58'),  # 成交额
                    'name': d.get('f58'),  # 股票名称
                }
            return {'success': False, 'error': '无数据'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_tencent(self, symbol: str) -> dict:
        """获取腾讯实时数据"""
        # 转换代码
        if symbol.startswith('6') or symbol.startswith('9'):
            code = f'sh{symbol}'
        else:
            code = f'sz{symbol}'
        
        url = f'https://qt.gtimg.cn/q={code}'
        
        try:
            r = self.session.get(url, timeout=5)
            data = r.text.split('~')
            
            return {
                'success': True,
                'price': float(data[3]) if data[3] else 0,
                'open': float(data[1]) if data[1] else 0,
                'high': float(data[4]) if data[4] else 0,
                'low': float(data[5]) if data[5] else 0,
                'volume': int(data[6]) if data[6] else 0,
                'amount': float(data[7]) if data[7] else 0,
                'name': data[1] if len(data) > 1 else ''
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}


# 测试
if __name__ == '__main__':
    print("=== 网络助手测试 ===\n")
    
    net = NetworkHelper()
    
    # 测试腾讯
    print("📊 腾讯实时:")
    result = net.get_tencent('300861')
    if result['success']:
        print(f"   {result['name']}: ¥{result['price']}")
    else:
        print(f"   错误: {result.get('error')}")
    
    # 测试东财
    print("\n📊 东财实时:")
    result = net.get_eastmoney('300861')
    if result['success']:
        print(f"   价格: ¥{result.get('price')}")
        print(f"   主力: {result.get('main_flow')}")
        print(f"   大单: {result.get('large_flow')}")
    else:
        print(f"   错误: {result.get('error')}")
