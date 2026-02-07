#!/bin/bash

set -e

echo "🚀 开始一键部署 OpenClaw..."

# 1. 克隆仓库
git clone git@github.com:Manstein17/--botbot.git botbot-setup
cd botbot-setup

# 2. 安装 OpenClaw（如果未安装）
if ! command -v openclaw &> /dev/null; then
    echo "📦 安装 OpenClaw..."
    npm install -g openclaw
fi

# 3. 恢复配置
echo "📄 恢复配置..."
cp openclaw-config.json ~/.openclaw/openclaw.json

# 4. 恢复 workspace
echo "📦 恢复 workspace..."
mkdir -p ~/.openclaw/workspace
rsync -av workspace/ ~/.openclaw/workspace/

# 5. 重启 Gateway
echo "🔄 重启 OpenClaw Gateway..."
openclaw gateway restart

echo ""
echo "✅ 部署完成！"
echo "运行 'openclaw status' 检查状态"
