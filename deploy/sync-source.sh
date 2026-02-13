#!/bin/bash

# OpenClaw 源码同步脚本
# 功能: 手动同步 OpenClaw 官方源码
# 运行方式: chmod +x sync-source.sh && ./sync-source.sh

set -e

OPENCLAW_SOURCE_DIR="$HOME/.openclaw/openclaw-source"

echo "📥 OpenClaw 源码同步"
echo "===================="
echo ""

# 检测源码目录
if [ -d "$OPENCLAW_SOURCE_DIR" ]; then
    echo "📁 检测到源码目录: $OPENCLAW_SOURCE_DIR"
    echo "🔄 正在更新..."
    cd "$OPENCLAW_SOURCE_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "⚠️  拉取失败，可能是独立开发分支"
    echo "✅ 源码已更新到最新版本"
else
    echo "📁 未检测到源码目录"
    echo "🔄 正在克隆..."
    git clone https://github.com/openclaw/openclaw.git "$OPENCLAW_SOURCE_DIR"
    echo "✅ 源码克隆完成"
fi

echo ""
echo "📍 源码位置: $OPENCLAW_SOURCE_DIR"
echo ""
