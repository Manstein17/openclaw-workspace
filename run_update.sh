#!/bin/bash
# 数据更新专用 - 绕过VPN代理

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
export no_proxy="*"

cd ~/.openclaw/workspace
source venv/bin/activate

exec python3 daily_update.py
