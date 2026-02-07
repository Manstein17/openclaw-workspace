#!/bin/bash

# BTC 每日汇总脚本
# 每天 20:00 自动执行

cd ~/.openclaw/workspace/projects/airdrop-intelligence-pro

# 搜索 BTC 新闻
echo "=== $(date) ===" >> ~/.openclaw/logs/daily-summary.log
echo "搜索 BTC 新闻..." >> ~/.openclaw/logs/daily-summary.log

# 获取今天日期
DATE=$(date +%Y-%m-%d)

# 搜索 BTC 新闻
BTC_NEWS=$(curl -s "https://api.brave.com/news/v1/headlines?q=bitcoin&age=1h&count=10" 2>/dev/null | head -c 500 || echo "搜索失败")

# 记录到 memory
cat >> ~/.openclaw/workspace/memory/${DATE}.md << 'MDEOF'

## BTC 每日汇总 - $(date +%Y-%m-%d)

### 主要新闻
$BTC_NEWS

### 市场情绪
（待补充）

### 关键事件
（待补充）

MDEOF

echo "汇总已生成" >> ~/.openclaw/logs/daily-summary.log
echo "下次运行: 明天 20:00" >> ~/.openclaw/logs/daily-summary.log
