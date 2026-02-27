#!/bin/bash
# A股交易系统自动运行脚本
# 每天 8:00 和 15:00 自动运行

cd /Users/manstein17/.openclaw/workspace

# 激活虚拟环境并运行
source venv/bin/activate
python trading_system_final.py >> /tmp/trading_system.log 2>&1

# 记录运行时间
echo "$(date '+%Y-%m-%d %H:%M:%S') - 系统已运行" >> /tmp/trading_system.log
