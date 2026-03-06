#!/bin/bash
# 检查 OpenClaw 更新并发送到 Discord 子区

CURRENT=$(openclaw --version 2>/dev/null)
LATEST=$(npm view openclaw version 2>/dev/null)

if [ "$CURRENT" != "$LATEST" ]; then
    echo "发现新版本: $LATEST (当前: $CURRENT)"
    # 这里可以调用 webhook 或让 agent 发送消息
else
    echo "已是最新版本: $CURRENT"
fi
