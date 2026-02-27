#!/bin/bash

# ==========================================
# 🎉 OpenClaw iCloud 备份脚本
# 自动将备份同步到 iCloud 云盘
# ==========================================

set -e

BACKUP_DIR="$HOME/.openclaw-backup"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/OpenClaw-Backup"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")

echo "=========================================="
echo "  ☁️ OpenClaw iCloud 备份"
echo "=========================================="
echo ""

# 1. 检查 iCloud 云盘是否可用
echo "📦 检查 iCloud 云盘..."
if [ ! -d "$ICLOUD_DIR" ]; then
    echo "📁 创建 iCloud 备份文件夹..."
    mkdir -p "$ICLOUD_DIR"
    echo "✅ 已创建: $ICLOUD_DIR"
else
    echo "✅ iCloud 云盘可用"
fi

# 2. 检查源目录
if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ 备份目录不存在: $BACKUP_DIR"
    exit 1
fi

# 3. 同步到 iCloud
echo ""
echo "📤 同步到 iCloud 云盘..."
rsync -avz --progress \
    --delete \
    "$BACKUP_DIR/" \
    "$ICLOUD_DIR/"

# 4. 创建时间戳文件
echo ""
echo "📅 记录备份时间..."
echo "$TIMESTAMP" > "$ICLOUD_DIR/.last-backup"

# 5. 检查 iCloud 同步状态
echo ""
echo "📊 iCloud 同步状态："
echo "   本地大小: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "   iCloud 大小: $(du -sh "$ICLOUD_DIR" | cut -f1)"
echo "   最后备份: $(cat "$ICLOUD_DIR/.last-backup" 2>/dev/null || echo '未知')"

echo ""
echo "=========================================="
echo "✅ iCloud 备份完成！"
echo "=========================================="
echo ""
echo "📁 iCloud 位置：$ICLOUD_DIR"
echo "🌐 访问方式：打开 iCloud 云盘文件夹"
echo "📅 时间：$TIMESTAMP"
echo ""
echo "💡 提示：iCloud 会自动同步到你的所有 Apple 设备"
echo "=========================================="
