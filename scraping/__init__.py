#!/usr/bin/env python3
"""
网页爬虫模块
提供股票数据抓取功能
"""

from .base import BaseScraper
from .sina import SinaKline, SinaRealtime
from .eastmoney import EastMoneyRealtime, EastMoneyKline
from .news import SinaNews, EastMoneyNews

__all__ = [
    'BaseScraper',
    'SinaKline',
    'SinaRealtime', 
    'EastMoneyRealtime',
    'EastMoneyKline',
    'SinaNews',
    'EastMoneyNews',
]

# 默认配置
DEFAULT_DELAY = 3.0  # 默认请求间隔（秒）
DEFAULT_TIMEOUT = 10  # 默认超时（秒）
