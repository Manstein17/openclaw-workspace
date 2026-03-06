#!/usr/bin/env python3
"""
基础爬虫类 - 优化版
已配置UA伪装和请求间隔
"""
import os
import time
import random
import requests
from typing import Optional, Dict, List, Any

# 禁用代理（金融API直连）
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)


# 浏览器User-Agent池
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
]


class BaseScraper:
    """爬虫基类 - 优化版"""
    
    # 类级别配置
    DEFAULT_DELAY = 3.0      # 默认请求间隔(秒)
    MAX_RETRIES = 3         # 最大重试次数
    RETRY_DELAY = 60        # 被限速后等待(秒)
    TIMEOUT = 10            # 超时时间(秒)
    
    def __init__(self, request_delay: float = None, timeout: int = None):
        self.session = requests.Session()
        self.session.trust_env = False  # 禁用系统代理
        
        # 设置请求头
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        })
        
        self.request_delay = request_delay or self.DEFAULT_DELAY
        self.timeout = timeout or self.TIMEOUT
        self.last_request_time = 0
        self.consecutive_errors = 0  # 连续错误计数
        
    def _wait(self):
        """等待间隔"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            wait_time = self.request_delay - elapsed + random.uniform(0, 1)
            time.sleep(wait_time)
        self.last_request_time = time.time()
    
    def _get(self, url: str, params: Optional[Dict] = None, 
             headers: Optional[Dict] = None, retry: int = None,
             allow_redirects: bool = True) -> Optional[requests.Response]:
        """发送GET请求 - 带重试机制"""
        
        retry = retry or self.MAX_RETRIES
        
        for attempt in range(retry):
            try:
                self._wait()
                
                # 随机切换User-Agent
                self.session.headers['User-Agent'] = random.choice(USER_AGENTS)
                
                response = self.session.get(
                    url, 
                    params=params, 
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=allow_redirects
                )
                
                # 检查状态码
                if response.status_code == 200:
                    self.consecutive_errors = 0
                    return response
                elif response.status_code == 403:
                    print(f"⚠️ 403 Forbidden (尝试 {attempt + 1}/{retry})")
                    time.sleep(self.RETRY_DELAY)
                elif response.status_code == 456:
                    # 新浪限速
                    print(f"⚠️ 456 限速! 等待{self.RETRY_DELAY}秒...")
                    time.sleep(self.RETRY_DELAY)
                    self.consecutive_errors += 1
                elif response.status_code == 429:
                    # 请求过多
                    print(f"⚠️ 429 Too Many Requests (尝试 {attempt + 1}/{retry})")
                    time.sleep(self.RETRY_DELAY * 2)
                else:
                    print(f"⚠️ 状态码 {response.status_code} (尝试 {attempt + 1}/{retry})")
                    
            except requests.exceptions.Timeout:
                print(f"⏱️ 超时 (尝试 {attempt + 1}/{retry})")
                time.sleep(5)
            except requests.exceptions.ConnectionError as e:
                print(f"❌ 连接错误: {str(e)[:50]} (尝试 {attempt + 1}/{retry})")
                time.sleep(10)
            except requests.exceptions.RequestException as e:
                print(f"❌ 请求失败: {str(e)[:50]} (尝试 {attempt + 1}/{retry})")
                time.sleep(5)
        
        self.consecutive_errors += 1
        return None
    
    def is_rate_limited(self) -> bool:
        """检查是否被限速"""
        return self.consecutive_errors >= 3
    
    def reset_error_count(self):
        """重置错误计数"""
        self.consecutive_errors = 0
    
    def _parse_html(self, response: requests.Response) -> Any:
        """解析HTML"""
        try:
            from bs4 import BeautifulSoup
            return BeautifulSoup(response.text, 'html.parser')
        except ImportError:
            return None
