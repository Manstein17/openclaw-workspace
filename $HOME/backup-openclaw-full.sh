#!/bin/bash

# ==========================================
# 🎉 OpenClaw 完整备份脚本
# 备份所有配置到 ~/.openclaw-backup/
# ==========================================

set -e

BACKUP_DIR="$HOME/.openclaw-backup"
OPENCLAW_DIR="$HOME/.openclaw"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

echo "=========================================="
echo "  🔒 OpenClaw 完整备份"
echo "=========================================="
echo ""

# 1. 创建备份目录
echo "📁 创建备份目录..."
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR/$(hostname)"
cd "$BACKUP_DIR"

# 2. 备份 OpenClaw 核心配置
echo "📦 备份 OpenClaw 核心配置..."

# 排除不需要备份的目录
EXCLUDE_DIRS="node_modules workspace/.git"

# 备份整个 OpenClaw 配置目录（排除 node_modules）
rsync -av --progress \
    --exclude='node_modules' \
    --exclude='.git' \
    "$OPENCLAW_DIR/" \
    "openclaw-full/"

# 3. 单独备份 workspace（完整）
echo "📦 备份 workspace..."
rm -rf workspace
cp -r "$OPENCLAW_DIR/workspace" .

# 4. 清理旧备份
echo "🧹 清理旧备份（保留最近3个）..."
ls -dt openclaw-full-* 2>/dev/null | tail -n +4 | xargs rm -rf 2>/dev/null || true

# 5. Git 提交并推送
echo ""
echo "=========================================="
echo "📤 推送到 GitHub..."
echo "=========================================="

cd "$BACKUP_DIR"

# 添加所有更改
git add -A

# 检查是否有更改
if git diff --cached --quiet; then
    echo "✅ 没有新更改，无需推送"
else
    # 提交
    git commit -m "完整备份 - $TIMESTAMP

包含：
- OpenClaw 核心配置（完整）
- workspace 所有文件
- 所有定时任务
- Telegram 配置
- Agent 配置
- Skills 配置"

    # 推送到 GitHub
    git push origin main

    echo ""
    echo "=========================================="
    echo "✅ 完整备份完成！"
    echo "=========================================="
    echo ""
    echo "📁 备份位置：$BACKUP_DIR"
    echo "🌐 GitHub：https://github.com/Manstein17/--botbot"
    echo "📅 时间：$TIMESTAMP"
fi

echo ""
echo "💡 提示：如需在新电脑部署，只需克隆 GitHub 仓库并运行 deploy.sh"
