#!/bin/bash
# OpenClaw 完整备份脚本（包含源码 + GitHub 同步）
# 每日 21:00 自动运行

BACKUP_DIR=~/.openclaw/backups
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE=~/.openclaw-backup.log
WORKSPACE=~/.openclaw/workspace

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "开始 OpenClaw 完整备份..."

# 0. 拉取 OpenClaw 官方源码
log "拉取 OpenClaw 官方源码..."
if [ -d "$HOME/.openclaw/openclaw-source" ]; then
    cd "$HOME/.openclaw/openclaw-source"
    git fetch origin
    if git diff --quiet origin/main --; then
        log "官方源码已是最新"
    else
        git pull origin main || log "⚠️ 源码更新失败"
    fi
else
    log "⚠️ 未找到官方源码目录，将克隆..."
    git clone https://github.com/openclaw/openclaw.git "$HOME/.openclaw/openclaw-source"
fi

# 0.1 进入工作区目录并确保 GitHub 同步
log "同步 GitHub 最新代码..."
cd "$WORKSPACE"
git fetch origin
# 如果有远程更新，先 pull
if ! git diff --quiet origin/main --; then
    log "发现远程更新，正在合并..."
    git pull origin main || git pull origin main --rebase || true
fi

# 1. 备份配置文件
log "备份配置文件..."
tar -czf "$BACKUP_DIR/config_${DATE}.tar.gz" \
    ~/.openclaw/openclaw.json \
    ~/.openclaw/workspace \
    ~/.openclaw/logs/gateway.log \
    2>/dev/null

# 2. 备份 OpenClaw 源码（官方源码）
log "备份 OpenClaw 源码..."
if [ -d "$HOME/.openclaw/openclaw-source" ]; then
    tar -czf "$BACKUP_DIR/openclaw_src_${DATE}.tar.gz" \
        "$HOME/.openclaw/openclaw-source" \
        2>/dev/null
elif [ -d "/opt/homebrew/lib/node_modules/openclaw" ]; then
    # 备用：备份 Homebrew 安装的版本
    tar -czf "$BACKUP_DIR/openclaw_src_${DATE}.tar.gz" \
        /opt/homebrew/lib/node_modules/openclaw \
        2>/dev/null
else
    log "⚠️ 未找到 OpenClaw 源码目录"
fi

# 3. 备份 LaunchAgent 配置
log "备份 LaunchAgent..."
cp ~/Library/LaunchAgents/ai.openclaw.gateway.plist \
    "$BACKUP_DIR/" 2>/dev/null

# 4. 清理旧备份（保留最近 7 天）
log "清理 7 天前的旧备份..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null

# 5. 检查 OpenClaw 更新
log "检查 OpenClaw 更新..."
CURRENT_VER=$(cat /opt/homebrew/lib/node_modules/openclaw/package.json 2>/dev/null | grep '"version"' | sed 's/.*: *"\([^"]*\)"/\1/')
log "当前版本: $CURRENT_VER"

# 列出备份文件
log "备份完成，文件列表:"
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | tail -5

# 6. 自动 commit + push 到 GitHub
log "提交到 GitHub..."
cd "$WORKSPACE"

# 添加备份信息文件
echo "Last backup: $(date)" > "$WORKSPACE/.last-backup"

git add -A

# 检查是否有更改
if git diff --cached --quiet; then
    log "没有需要提交的更改"
else
    git commit -m "Auto backup $(date '+%Y-%m-%d %H:%M')"
    if git push origin main 2>/dev/null; then
        log "✅ GitHub 同步成功"
    else
        log "⚠️ GitHub 同步失败（可能网络问题）"
    fi
fi

log "✅ 备份成功"
