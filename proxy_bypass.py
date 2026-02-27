"""
代理绕过配置
"""
import os

# 清除所有代理设置
proxy_vars = [
    'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY',
    'ALL_PROXY', 'all_proxy',
]

for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]

# 设置不过滤的域名（空 = 不过滤）
os.environ['NO_PROXY'] = ''
os.environ['no_proxy'] = ''

# 强制不使用代理
import requests
requests.Session(trust_env=False)

print("✅ 代理已绕过")
