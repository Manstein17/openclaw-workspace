#!/bin/bash

# OpenClaw Android (Termux) 部署脚本
# 运行方式: chmod +x android.sh && ./android.sh

set -e

echo "📱 欢迎使用 OpenClaw Android 部署脚本！"
echo "========================================"

# 检查是否在 Termux 环境中
if ! command -v termux-info &> /dev/null && [ -z "$TERMUX_VERSION" ]; then
    echo "⚠️  请在 Termux 中运行此脚本"
    echo "📥 下载 Termux: https://f-droid.org/packages/com.termux/"
    exit 1
fi

# 更新包列表
echo "📦 更新包列表..."
apt update

# 安装基础依赖
echo "📦 安装系统依赖..."
apt install -y git curl wget build-essential python

# 安装 Node.js 20
echo "📦 安装 Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# 检查 Node.js 版本
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Node.js 版本过低，请手动更新"
fi

# 安装 OpenClaw
echo "📦 安装 OpenClaw..."
npm install -g openclaw

# 创建工作目录
WORK_DIR="$HOME/openclaw"
echo "📁 创建工作目录: $WORK_DIR"
mkdir -p $WORK_DIR
cd $WORK_DIR

# 克隆仓库
echo "📥 克隆 OpenClaw 仓库..."
if [ -d ".git" ]; then
    echo "📁 仓库已存在，更新中..."
    git pull
else
    git clone https://github.com/Manstein17/--botbot.git .
fi

# 安装依赖
echo "📦 安装 Node.js 依赖..."
npm install

# 配置 OpenClaw
echo "⚙️  配置 OpenClaw..."
if [ ! -f "openclaw-config.json" ]; then
    cp openclaw-config.json.example openclaw-config.json 2>/dev/null || true
fi

echo ""
echo "✅ Android (Termux) 部署完成！"
echo "📖 查看部署文档: $WORK_DIR/deploy/android-deploy.md"
echo ""
echo "启动命令:"
echo "  openclaw gateway start"
echo ""
echo "注意: Termux 需要保持运行才能使用 OpenClaw"
echo "建议使用 Termux:Boot 或 Tasker 实现开机自启"
