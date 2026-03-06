#!/usr/bin/env python3
"""
实时新闻获取模块
对标daily_stock_analysis项目
"""
import os
import time
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict

# 禁用代理
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

class RealtimeNewsFetcher:
    """实时财经新闻获取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.news_cache = []
        self.last_fetch = None
    
    def fetch_sina_finance(self) -> List[Dict]:
        """获取新浪财经新闻"""
        news_list = []
        
        try:
            url = 'https://finance.sina.com.cn/stock/'
            r = self.session.get(url, timeout=10)
            r.encoding = 'utf-8'
            
            if r.status_code == 200:
                import re
                titles = re.findall(r'title=\"([^\"]{10,80})\"', r.text)
                
                for title in set(titles):
                    if len(title) > 10 and any(x in title for x in ['股', '市', '涨', '跌', '政策', '利好', '利空']):
                        news_list.append({
                            'title': title[:60],
                            'url': '',
                            'source': '新浪财经',
                            'time': datetime.now().strftime('%H:%M')
                        })
        except Exception as e:
            print(f"新浪新闻获取失败: {e}")
        
        return news_list[:10]
    
    def fetch_eastmoney(self) -> List[Dict]:
        """获取东财新闻"""
        news_list = []
        
        try:
            url = 'https://stock.eastmoney.com/'
            r = self.session.get(url, timeout=10)
            
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                
                for item in soup.select('.news_list a, .article-item a, .title a')[:10]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')
                    
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'url': href,
                            'source': '东方财富',
                            'time': datetime.now().strftime('%H:%M')
                        })
        except Exception as e:
            print(f"东财新闻获取失败: {e}")
        
        return news_list
    
    def fetch_xueqiu(self) -> List[Dict]:
        """获取雪球新闻"""
        news_list = []
        
        try:
            # 雪球热门话题
            url = 'https://xueqiu.com/statuses/hot.json?type=stock'
            r = self.session.get(url, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                for item in data.get('list', [])[:10]:
                    news_list.append({
                        'title': item.get('text', '')[:100],
                        'url': f'https://xueqiu.com/S/{item.get("symbol", "")}',
                        'source': '雪球',
                        'time': datetime.now().strftime('%H:%M')
                    })
        except Exception as e:
            print(f"雪球新闻获取失败: {e}")
        
        return news_list
    
    def fetch_10jqka(self) -> List[Dict]:
        """获取同花顺新闻"""
        news_list = []
        
        try:
            url = 'https://www.10jqka.com.cn/news/'
            r = self.session.get(url, timeout=10)
            
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                
                for item in soup.select('.news_list a, .cont a, .title a')[:10]:
                    title = item.get_text(strip=True)
                    href = item.get('href', '')
                    
                    if title and len(title) > 5:
                        news_list.append({
                            'title': title,
                            'url': href,
                            'source': '同花顺',
                            'time': datetime.now().strftime('%H:%M')
                        })
        except Exception as e:
            print(f"同花顺新闻获取失败: {e}")
        
        return news_list
    
    def fetch_all(self, force=False) -> List[Dict]:
        """获取所有来源的新闻"""
        # 检查缓存（5分钟内不重复获取）
        if not force and self.last_fetch:
            elapsed = (datetime.now() - self.last_fetch).seconds
            if elapsed < 300 and self.news_cache:
                return self.news_cache
        
        all_news = []
        
        # 获取各来源新闻
        all_news.extend(self.fetch_sina_finance())
        all_news.extend(self.fetch_eastmoney())
        
        # 去重
        seen = set()
        unique_news = []
        for n in all_news:
            if n['title'] not in seen:
                seen.add(n['title'])
                unique_news.append(n)
        
        self.news_cache = unique_news
        self.last_fetch = datetime.now()
        
        return unique_news
    
    def get_market_news(self) -> str:
        """获取市场新闻摘要"""
        news = self.fetch_all()
        
        if not news:
            return "暂无新闻"
        
        # 取最新5条
        latest = news[:5]
        
        msg = "📰 **实时财经新闻**\n\n"
        for i, n in enumerate(latest, 1):
            msg += f"{i}. {n['title'][:50]}...\n"
            msg += f"   来源: {n['source']}\n\n"
        
        return msg


# 测试
if __name__ == '__main__':
    print("=== 实时新闻测试 ===\n")
    
    fetcher = RealtimeNewsFetcher()
    
    print("📥 获取新闻...")
    news = fetcher.fetch_all()
    
    print(f"获取到 {len(news)} 条新闻\n")
    
    for i, n in enumerate(news[:10], 1):
        print(f"{i}. [{n['source']}] {n['title'][:50]}")
