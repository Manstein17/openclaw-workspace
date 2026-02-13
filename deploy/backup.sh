#!/bin/bash

# OpenClaw 完整备份脚本
# 功能: 备份 ~/.openclaw/、workspace/、源码 到指定位置
# 运行方式: chmod +x backup.sh && ./backup.sh
# 参数: ./backup.sh [备份目录] (可选，默认 ~/OpenClaw-Backups)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 备份目录
if [ -n "$1" ]; then
    BACKUP_BASE="$1"
else
    BACKUP_BASE="$HOME/OpenClaw-Backups"
fi

BACKUP_DIR="$BACKUP_BASE/backup-$(date +%Y%m%d-%H%M%S)"

echo "📦 OpenClaw 完整备份"
echo "===================="
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 统计备份内容
TOTAL_ITEMS=0

# 1. 备份 ~/.openclaw/ 整个目录
echo "📁 备份 ~/.openclaw/ ..."
if [ -d "$HOME/.openclaw" ]; then
    cp -r "$HOME/.openclaw" "$BACKUP_DIR/"
    ITEM_COUNT=$(find "$BACKUP_DIR/.openclaw" -type f 2>/dev/null | wc -l)
    TOTAL_ITEMS=$((TOTAL_ITEMS + ITEM_COUNT))
    echo -e "  ${GREEN}✅ 备份完成 ($ITEM_COUNT 个文件)${NC}"
else
    echo -e "  ${YELLOW}⚠️  目录不存在，跳过${NC}"
fi

# 2. 备份 OpenClaw 源码（如果存在）
echo "📁 备份 OpenClaw 源码 ..."
if [ -d "$HOME/.openclaw/openclaw-source" ]; then
    cp -r "$HOME/.openclaw/openclaw-source" "$BACKUP_DIR/"
    ITEM_COUNT=$(find "$BACKUP_DIR/openclaw-source" -type f 2>/dev/null | wc -l)
    TOTAL_ITEMS=$((TOTAL_ITEMS + ITEM_COUNT))
    echo -e "  ${GREEN}✅ 源码备份完成 ($ITEM_COUNT 个文件)${NC}"
else
    echo -e "  ${YELLOW}⚠️  源码目录不存在，跳过${NC}"
fi

# 3. 创建备份信息文件
cat > "$BACKUP_DIR/backup-info.txt" << EOF
OpenClaw 完整备份信息
=====================
备份时间: $(date)
主机名: $(hostname)
操作系统: $(uname -s) $(uname -r)

📋 备份内容:
• ~/.openclaw/ - 完整配置目录 (包含所有配置、技能、脚本)
• ~/.openclaw/openclaw-source/ - OpenClaw 官方源码

🔧 恢复命令:
# 恢复配置
cp -r "$BACKUP_DIR/.openclaw" $HOME/

# 或选择性恢复
cp -r "$BACKUP_DIR/.openclaw/workspace" $HOME/.openclaw/
cp -r "$BACKUP_DIR/.openclaw/openclaw-config.json" $HOME/.openclaw/ 2>/dev/null || true

📊 统计:
总文件数: $TOTAL_ITEMS
EOF

echo ""
echo -e "${GREEN}✅ 备份完成！${NC}"
echo ""
echo "📍 备份位置: $BACKUP_DIR"
echo "📊 备份文件数: $TOTAL_ITEMS"
echo ""
echo "🔧 恢复命令:"
echo "  cp -r $BACKUP_DIR/.openclaw \$HOME/"
echo ""
echo "💡 提示: 建议定期执行备份，并将备份文件保存到云盘或外部存储"
