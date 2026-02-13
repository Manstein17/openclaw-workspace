#!/bin/bash

# OpenClaw Linux 桌面部署脚本
# 运行方式: chmod +x linux.sh && ./linux.sh

set -e

echo "🐧 欢迎使用 OpenClaw Linux 桌面部署脚本！"
echo "=========================================="

# 检测包管理器
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    INSTALL_CMD="sudo apt-get install -y"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
elif command -v zypper &> /dev/null; then
    PKG_MANAGER="zypper"
    INSTALL_CMD="sudo zypper install -y"
else
    echo "❌ 不支持的 Linux 发行版"
    exit 1
fi

echo "📦 检测到包管理器: $PKG_MANAGER"

# 安装依赖
echo "📦 安装系统依赖..."
$INSTALL_CMD git curl wget build-essential

# 安装 Node.js 18+
if ! command -v node &> /dev/null; then
    echo "📦 安装 Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    $INSTALL_CMD nodejs
fi

# 检查 Node.js 版本
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Node.js 版本过低，正在更新..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    $INSTALL_CMD nodejs
fi

# 安装 OpenClaw CLI
if ! command -v openclaw &> /dev/null; then
    echo "📦 安装 OpenClaw CLI..."
    sudo npm install -g openclaw
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
echo "📖 查看部署文档: openclaw/deploy/linux-deploy.md"
