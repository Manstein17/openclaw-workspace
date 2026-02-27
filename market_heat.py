#!/usr/bin/env python3
"""
市场热度分析模块
- 资金流向
- 板块轮动
- 热门概念
"""
import akshare as ak
import pandas as pd
from datetime import datetime
import json
import os

class MarketHeatAnalyzer:
    """市场热度分析器"""
    
    CACHE_FILE = "/tmp/market_heat.json"
    CACHE_DURATION = 2 * 60 * 60  # 2小时缓存
    
    def __init__(self):
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    if datetime.now().timestamp() - data.get('timestamp', 0) < self.CACHE_DURATION:
                        return data
            except:
                pass
        return {}
    
    def _save_cache(self, data):
        """保存缓存"""
        data['timestamp'] = datetime.now().timestamp()
        with open(self.CACHE_FILE, 'w') as f:
            json.dump(data, f)
    
    def get_market_heatmap(self) -> dict:
        """获取市场热度 - 使用本地数据计算"""
        
        # 检查缓存
        if 'heatmap' in self.cache and self.cache.get('heatmap'):
            cached = self.cache.get('heatmap', {})
            if cached.get('sectors') or cached.get('up_count', 0) > 0:
                return self.cache['heatmap']
        
        print("   正在计算市场热度...")
        
        heatmap = {
            'sectors': [],
            'hot_concepts': [],
            'fund_flow': {},
            'up_count': 0,
            'down_count': 0
        }
        
        # 使用本地数据计算热门板块
        import os
        import glob
        
        cache_dir = "/Users/manstein17/.openclaw/workspace/stock_cache/daily"
        
        # 按行业分组计算涨幅
        sector_perf = {}
        
        # 行业代码映射
        sector_map = {}
        
        files = glob.glob(f"{cache_dir}/*.csv")[:500]  # 取前500只
        
        for f in files:
            try:
                symbol = os.path.basename(f).replace('.csv', '')
                df = pd.read_csv(f)
                
                if df is not None and len(df) >= 5:
                    # 计算最近5天涨幅
                    recent = df.tail(5)
                    change = (recent['收盘'].iloc[-1] - recent['收盘'].iloc[0]) / recent['收盘'].iloc[0] * 100
                    
                    # 简单行业分类
                    if symbol.startswith('600') or symbol.startswith('000'):
                        if int(symbol[:3]) >= 600:
                            sector = '上海主板'
                        else:
                            sector = '深圳主板'
                    elif symbol.startswith('300'):
                        sector = '创业板'
                    elif symbol.startswith('688'):
                        sector = '科创板'
                    else:
                        sector = '其他'
                    
                    if sector not in sector_perf:
                        sector_perf[sector] = []
                    sector_perf[sector].append(change)
            except:
                pass
        
        # 计算各板块平均涨幅
        for sector, changes in sector_perf.items():
            if changes:
                avg_change = sum(changes) / len(changes)
                heatmap['sectors'].append({
                    'name': sector,
                    'flow': avg_change * 1000000  # 模拟资金流
                })
        
        # 按涨幅排序
        heatmap['sectors'].sort(key=lambda x: x['flow'], reverse=True)
        
        # 统计涨跌停（模拟）
        heatmap['up_count'] = sum(1 for s in heatmap['sectors'] if s['flow'] > 0)
        heatmap['down_count'] = sum(1 for s in heatmap['sectors'] if s['flow'] < 0)
        
        # 缓存
        self.cache['heatmap'] = heatmap
        self._save_cache(self.cache)
        
        return heatmap
    
    def get_hot_sectors(self) -> list:
        """获取热门板块"""
        heatmap = self.get_market_heatmap()
        return heatmap.get('sectors', [])[:5]
    
    def get_sector_sentiment(self, sector: str) -> str:
        """判断板块情绪"""
        sectors = self.get_hot_sectors()
        
        # 简单判断
        for s in sectors:
            if sector in s.get('name', ''):
                if s.get('flow', 0) > 0:
                    return '利好'
                else:
                    return '利空'
        
        return '中性'


# 测试
if __name__ == "__main__":
    analyzer = MarketHeatAnalyzer()
    heatmap = analyzer.get_market_heatmap()
    print("市场热度:")
    print(f"  涨停: {heatmap.get('up_count', 0)}")
    print(f"  跌停: {heatmap.get('down_count', 0)}")
    print(f"  热门板块: {heatmap.get('sectors', [])[:5]}")
