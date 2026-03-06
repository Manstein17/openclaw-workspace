#!/usr/bin/env python3
"""
新浪财经K线数据爬虫 - 优化版
针对456限速做了优化
"""
import pandas as pd
from typing import Optional, List, Dict
from .base import BaseScraper


class SinaKline(BaseScraper):
    """新浪财经K线数据 - 优化版"""
    
    def __init__(self, request_delay: float = 5.0):
        """
        初始化
        
        Args:
            request_delay: 请求间隔(秒)，默认5秒避免456
        """
        super().__init__(request_delay=request_delay)
        self.base_url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
    
    def get(self, symbol: str, scale: str = '240', limit: int = 30) -> Optional[List[Dict]]:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码 (如 sh600000, sz000001)
            scale: K线周期 (60/240/1440/10080/month)
            limit: 获取数量
        
        Returns:
            K线数据列表，失败返回None
        """
        # 处理股票代码
        if not symbol.startswith('sh') and not symbol.startswith('sz'):
            symbol = f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}'
        
        params = {
            'symbol': symbol,
            'scale': scale,
            'ma': 'no',
            'datalen': str(limit)
        }
        
        # 添加Referer
        headers = {
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        response = self._get(self.base_url, params, headers)
        
        if response is None:
            return None
        
        try:
            data = response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            # 检查456错误
            if isinstance(data, dict) and data.get('err'):
                print(f"⚠️ 新浪错误: {data.get('err')}")
                return None
            
            # 转换为标准格式
            klines = []
            for item in data:
                try:
                    klines.append({
                        'date': item.get('day'),
                        'open': float(item.get('open', 0)),
                        'close': float(item.get('close', 0)),
                        'high': float(item.get('high', 0)),
                        'low': float(item.get('low', 0)),
                        'volume': int(item.get('volume', 0)),
                    })
                except (ValueError, TypeError):
                    continue
            
            if klines:
                self.reset_error_count()
                return klines
            return None
            
        except Exception as e:
            print(f"❌ 解析失败: {e}")
            return None
    
    def get_with_retry(self, symbol: str, max_retries: int = 5) -> Optional[List[Dict]]:
        """
        带重试的获取
        
        Args:
            symbol: 股票代码
            max_retries: 最大重试次数
        
        Returns:
            K线数据
        """
        for i in range(max_retries):
            result = self.get(symbol)
            if result:
                return result
            
            wait_time = 60 * (i + 1)  # 递增等待
            print(f"等待 {wait_time} 秒后重试 ({i+1}/{max_retries})...")
            time.sleep(wait_time)
        
        return None
    
    def to_dataframe(self, symbol: str, limit: int = 30) -> Optional[pd.DataFrame]:
        """获取DataFrame格式"""
        klines = self.get(symbol, limit=limit)
        
        if klines is None:
            return None
        
        return pd.DataFrame(klines)


class SinaRealtime(BaseScraper):
    """新浪实时行情 - 优化版"""
    
    def __init__(self, request_delay: float = 3.0):
        super().__init__(request_delay=request_delay)
        self.base_url = 'https://hq.sinajs.cn/list='
    
    def get(self, symbol: str) -> Optional[Dict]:
        """获取实时行情"""
        # 处理股票代码
        if not symbol.startswith('sh') and not symbol.startswith('sz'):
            symbol = f'sh{symbol}' if symbol.startswith('6') else f'sz{symbol}'
        
        url = self.base_url + symbol
        
        headers = {
            'Referer': 'https://finance.sina.com.cn/'
        }
        
        response = self._get(url, headers=headers)
        
        if response is None:
            return None
        
        try:
            text = response.text
            if 'var_hq_str' not in text:
                return None
            
            # 解析数据
            data = text.split('=')[1].strip('";\n').split(',')
            
            if len(data) < 10:
                return None
            
            return {
                'symbol': symbol,
                'name': data[0],
                'open': float(data[1]) if data[1] else 0,
                'close': float(data[2]) if data[2] else 0,
                'price': float(data[3]) if data[3] else 0,
                'high': float(data[4]) if data[4] else 0,
                'low': float(data[5]) if data[5] else 0,
                'volume': int(float(data[6])) if data[6] else 0,
                'amount': float(data[7]) if data[7] else 0,
            }
            
        except Exception as e:
            return None


if __name__ == '__main__':
    # 测试
    print("测试 SinaKline...")
    sina = SinaKline(request_delay=5)
    klines = sina.get('sh600000', limit=5)
    
    if klines:
        for k in klines:
            print(f"{k['date']}: {k['close']}")
    else:
        print("获取失败")
