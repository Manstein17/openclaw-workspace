#!/usr/bin/env python3
"""
东方财富数据爬虫
"""
import pandas as pd
from typing import Optional, List, Dict
from .base import BaseScraper


class EastMoneyRealtime(BaseScraper):
    """东方财富实时行情"""
    
    def __init__(self, request_delay: float = 3.0):
        super().__init__(request_delay)
        self.base_url = 'https://qt.gtimg.cn/q='
    
    def get(self, symbol: str) -> Optional[Dict]:
        """
        获取实时行情
        
        Args:
            symbol: 股票代码
        
        Returns:
            实时行情数据
        """
        # 处理股票代码
        if not symbol.startswith('sh') and not symbol.startswith('sz'):
            symbol = f'sh{symbol}' if symbol.startswith('6') or symbol.startswith('9') else f'sz{symbol}'
        
        url = self.base_url + symbol
        response = self._get(url)
        
        if response is None or 'v_' not in response.text:
            return None
        
        try:
            text = response.text
            data = text.split('=')[1].split('~')
            
            return {
                'symbol': symbol,
                'name': data[0],
                'price': float(data[3]) if data[3] else 0,
                'prev_close': float(data[4]) if data[4] else 0,
                'open': float(data[5]) if data[5] else 0,
                'volume': int(float(data[6])) if data[6] else 0,
                'amount': float(data[7]) if data[7] else 0,
                'high': float(data[33]) if data[33] else 0,
                'low': float(data[34]) if data[34] else 0,
            }
            
        except Exception as e:
            print(f"解析失败: {e}")
            return None
    
    def batch_get(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取实时行情"""
        results = {}
        
        for symbol in symbols:
            data = self.get(symbol)
            if data:
                results[symbol] = data
            print(f"  已获取: {symbol}")
        
        return results


class EastMoneyKline(BaseScraper):
    """东方财富K线数据"""
    
    def __init__(self, request_delay: float = 3.0):
        super().__init__(request_delay)
        self.base_url = 'https://push2.eastmoney.com/api/qt/stock/kline/get'
    
    def get(self, symbol: str, start_date: str = '20250101', 
            end_date: str = '20260304', limit: int = 30) -> Optional[List[Dict]]:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码 (如 600000)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            limit: 数量限制
        
        Returns:
            K线数据列表
        """
        # 处理股票代码 (需要加上市场前缀: 0.深圳 1.上海)
        if symbol.startswith('6') or symbol.startswith('9'):
            secid = f'1.{symbol}'  # 上海
        else:
            secid = f'0.{symbol}'  # 深圳
        
        params = {
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',  # 日K
            'fqt': '0',   # 不复权
            'secid': secid,
            'beg': start_date,
            'end': end_date,
            'lmt': str(limit)
        }
        
        response = self._get(self.base_url, params)
        
        if response is None:
            return None
        
        try:
            data = response.json()
            
            if not data.get('data'):
                return None
            
            klines = data['data']['klines']
            
            # 解析数据
            result = []
            for kline in klines:
                parts = kline.split(',')
                result.append({
                    'date': parts[0],
                    'open': float(parts[1]),
                    'close': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'volume': int(parts[5]),
                    'amount': float(parts[6]),
                })
            
            return result
            
        except Exception as e:
            print(f"解析失败: {e}")
            return None
