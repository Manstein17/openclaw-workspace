#!/bin/bash
# 交易系统专用 - 绕过VPN代理

# 清除代理环境变量
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy

# 设置直连
export no_proxy="*"

# 激活虚拟环境并运行
cd ~/.openclaw/workspace
source venv/bin/activate

# 运行交易系统
exec python3 realtime_trader.py
