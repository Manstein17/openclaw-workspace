#!/bin/bash

# OpenClaw Linux 桌面部署脚本
# 运行方式: chmod +x linux.sh && ./linux.sh
# 功能: 一键部署 + 自动同步官方源码 + 完整备份

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🐧 欢迎使用 OpenClaw Linux 桌面部署脚本！"
echo "=========================================="
echo ""

# ============================================
# 第 1 部分：完整备份（部署前必做）
# ============================================
echo -e "${YELLOW}📦 第 1 步：备份现有数据...${NC}"

BACKUP_DIR="$HOME/openclaw-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 备份 ~/.openclaw/ 整个目录
if [ -d "$HOME/.openclaw" ]; then
    echo "  📁 备份 ~/.openclaw/ ..."
    cp -r "$HOME/.openclaw" "$BACKUP_DIR/"
    echo -e "  ${GREEN}✅ ~/.openclaw/ 备份完成${NC}"
fi

# 备份 workspace/ 目录
if [ -d "$HOME/.openclaw/workspace" ]; then
    echo "  📁 备份 workspace/ ..."
    cp -r "$HOME/.openclaw/workspace" "$BACKUP_DIR/"
    echo -e "  ${GREEN}✅ workspace/ 备份完成${NC}"
fi

# 备份 OpenClaw 源码（如果存在）
if [ -d "$HOME/openclaw" ]; then
    echo "  📁 备份 OpenClaw 源码 ..."
    cp -r "$HOME/openclaw" "$BACKUP_DIR/openclaw-source"
    echo -e "  ${GREEN}✅ OpenClaw 源码备份完成${NC}"
fi

# 创建备份信息文件
cat > "$BACKUP_DIR/backup-info.txt" << EOF
OpenClaw 备份信息
==================
备份时间: $(date)
主机名: $(hostname)
操作系统: $(uname -a)
OpenClaw 目录: $HOME/.openclaw
工作区: $HOME/.openclaw/workspace
源码: $HOME/openclaw (如果存在)

备份内容:
- ~/.openclaw/ (完整配置)
- ~/.openclaw/workspace/ (工作文件)
- ~/openclaw/ (源码, 如果存在)

恢复命令:
cp -r $BACKUP_DIR/.openclaw $HOME/
cp -r $BACKUP_DIR/workspace $HOME/.openclaw/
EOF

echo -e "${GREEN}  ✅ 备份完成！备份位置: $BACKUP_DIR${NC}"
echo ""

# ============================================
# 第 2 部分：同步 OpenClaw 官方源码
# ============================================
echo -e "${YELLOW}📥 第 2 步：同步 OpenClaw 官方源码...${NC}"

OPENCLAW_SOURCE_DIR="$HOME/.openclaw/openclaw-source"

if [ -d "$OPENCLAW_SOURCE_DIR" ]; then
    echo "  📁 检测到已有源码目录，更新中..."
    cd "$OPENCLAW_SOURCE_DIR"
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "  ⚠️  拉取失败，可能是独立开发分支"
    echo -e "  ${GREEN}✅ 源码已更新${NC}"
else
    echo "  📥 克隆 OpenClaw 官方源码..."
    git clone https://github.com/openclaw/openclaw.git "$OPENCLAW_SOURCE_DIR"
    echo -e "  ${GREEN}✅ 源码克隆完成${NC}"
fi
echo ""

# ============================================
# 第 3 部分：检测包管理器并安装依赖
# ============================================
echo -e "${YELLOW}📦 第 3 步：安装系统依赖...${NC}"

if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    INSTALL_CMD="sudo apt-get install -y"
    echo "  检测到包管理器: apt (Ubuntu/Debian)"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
    echo "  检测到包管理器: dnf (Fedora/RHEL)"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
    echo "  检测到包管理器: pacman (Arch/Manjaro)"
elif command -v zypper &> /dev/null; then
    PKG_MANAGER="zypper"
    INSTALL_CMD="sudo zypper install -y"
    echo "  检测到包管理器: zypper (openSUSE)"
else
    echo -e "${RED}❌ 不支持的 Linux 发行版${NC}"
    exit 1
fi

# 安装基础工具
$INSTALL_CMD git curl wget build-essential

# 安装 Node.js
if ! command -v node &> /dev/null; then
    echo "  📦 安装 Node.js..."
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        $INSTALL_CMD nodejs
    elif [ "$PKG_MANAGER" = "dnf" ]; then
        curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
        $INSTALL_CMD nodejs
    elif [ "$PKG_MANAGER" = "pacman" ]; then
        $INSTALL_CMD nodejs npm
    fi
fi

# 检查 Node.js 版本
NODE_VERSION=$(node -v 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)
if [ -n "$NODE_VERSION" ] && [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "  ${YELLOW}⚠️  Node.js 版本过低，正在更新...${NC}"
    if [ "$PKG_MANAGER" = "apt-get" ]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        $INSTALL_CMD nodejs
    fi
fi

echo -e "${GREEN}  ✅ 依赖安装完成${NC}"
echo ""

# ============================================
# 第 4 部分：配置 OpenClaw
# ============================================
echo -e "${YELLOW}⚙️  第 4 步：配置 OpenClaw...${NC}"

# 确保 ~/.openclaw 目录存在
mkdir -p "$HOME/.openclaw"

# 如果有源码，复制配置文件
if [ -d "$OPENCLAW_SOURCE_DIR" ]; then
    if [ -f "$OPENCLAW_SOURCE_DIR/openclaw-config.json.example" ]; then
        cp "$OPENCLAW_SOURCE_DIR/openclaw-config.json.example" "$HOME/.openclaw/openclaw-config.json" 2>/dev/null || true
    fi
fi

echo -e "${GREEN}  ✅ 配置完成${NC}"
echo ""

# ============================================
# 第 5 部分：启动 OpenClaw
# ============================================
echo -e "${YELLOW}🚀 第 5 步：启动 OpenClaw Gateway...${NC}"

# 尝试启动
if command -v openclaw &> /dev/null; then
    openclaw gateway start
else
    echo -e "${YELLOW}  ⚠️  openclaw 命令未找到，请先安装 OpenClaw CLI${NC}"
    echo "  安装命令: sudo npm install -g openclaw"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "📋 摘要:"
echo "  • 备份位置: $BACKUP_DIR"
echo "  • 源码位置: $OPENCLAW_SOURCE_DIR"
echo "  • 配置目录: $HOME/.openclaw"
echo ""
echo "📖 后续操作:"
echo "  • 查看部署文档: openclaw deploy/linux-deploy.md"
echo "  • 启动命令: openclaw gateway start"
echo "  • 停止命令: openclaw gateway stop"
echo "  • 状态查看: openclaw gateway status"
echo ""
echo "🔄 更新源码:"
echo "  • 自动更新: ~/.openclaw/workspace/deploy/sync-source.sh"
echo ""
