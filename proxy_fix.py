#!/usr/bin/env python3
"""
代理配置 - 确保不通过代理访问数据接口
"""
import os
import sys

# 清除所有代理环境变量
proxy_vars = [
    'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',
    'http_proxy_user', 'https_proxy_user',
    'http_proxy_pass', 'https_proxy_pass',
    'ALL_PROXY', 'all_proxy',
    'NO_PROXY', 'no_proxy'
]

for var in proxy_vars:
    os.environ.pop(var, None)

# 强制不使用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

# 禁用requests的代理环境读取
import requests
try:
    session = requests.Session()
    session.trust_env = False
except:
    pass

# 打印确认
print("代理配置已清除:")
for var in proxy_vars:
    if var not in os.environ:
        print(f"  ✓ {var} 已清除")
