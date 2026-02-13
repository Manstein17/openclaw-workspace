#!/bin/bash

# OpenClaw macOS 部署脚本
# 运行方式: chmod +x mac.sh && ./mac.sh

set -e

echo "🍎 欢迎使用 OpenClaw macOS 部署脚本！"
echo "========================================"

# 检查 Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 正在安装 Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 安装依赖
echo "📦 安装依赖..."
brew install node git python

# 检查 Node.js 版本
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Node.js 版本过低，正在更新..."
    brew install node@20
    brew link node@20 --force
fi

# 克隆仓库
echo "📥 克隆 OpenClaw 仓库..."
if [ -d "openclaw" ]; then
    echo "📁 openclaw 目录已存在，跳过克隆"
    cd openclaw
else
    git clone https://github.com/Manstein17/--botbot.git openclaw
    cd openclaw
fi

# 安装依赖
echo "📦 安装 Node.js 依赖..."
npm install

# 配置 OpenClaw
echo "⚙️  配置 OpenClaw..."
if [ ! -f "openclaw-config.json" ]; then
    cp openclaw-config.json.example openclaw-config.json 2>/dev/null || true
fi

# 启动 OpenClaw
echo "🚀 启动 OpenClaw Gateway..."
openclaw gateway start

echo ""
echo "✅ 部署完成！"
echo "📖 查看部署文档: openclaw deploy/mac-deploy.md"
