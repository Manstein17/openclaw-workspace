#!/bin/bash

# OpenClaw 源码同步脚本
# 功能: 自动检测并同步 OpenClaw 官方源码
# 位置: ~/.openclaw/workspace/deploy/backup/sync-official-source.sh
# 运行: chmod +x sync-official-source.sh && ./sync-official-source.sh

set -euo pipefail

# ============================================
# 颜色定义
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================
# 配置
# ============================================
OPENCLAW_SOURCE_DIR="${HOME}/.openclaw/openclaw-source"
GITHUB_REPO="https://github.com/openclaw/openclaw.git"
LOG_FILE="${HOME}/.openclaw/logs/sync-source.log"

# ============================================
# 日志函数
# ============================================
log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 确保日志目录存在
    mkdir -p "$(dirname "$LOG_FILE")"
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    case "$level" in
        INFO)
            echo -e "${GREEN}[$timestamp] ✅ $message${NC}"
            ;;
        WARN)
            echo -e "${YELLOW}[$timestamp] ⚠️  $message${NC}"
            ;;
        ERROR)
            echo -e "${RED}[$timestamp] ❌ $message${NC}"
            ;;
        *)
            echo -e "${BLUE}[$timestamp] ℹ️  $message${NC}"
            ;;
    esac
}

# ============================================
# 检测网络连接
# ============================================
check_network() {
    log INFO "检测网络连接..."
    if curl -s --max-time 10 https://github.com > /dev/null 2>&1; then
        log INFO "网络连接正常"
        return 0
    else
        log WARN "网络连接失败，将使用缓存的源码"
        return 1
    fi
}

# ============================================
# 检测源码目录状态
# ============================================
detect_source_status() {
    if [ -d "$OPENCLAW_SOURCE_DIR" ]; then
        if [ -d "$OPENCLAW_SOURCE_DIR/.git" ]; then
            echo "existing_git"
        else
            echo "existing_manual"
        fi
    else
        echo "not_exists"
    fi
}

# ============================================
# 获取远程最新提交信息
# ============================================
get_remote_info() {
    cd "$OPENCLAW_SOURCE_DIR"
    
    local branch
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "main")
    
    local remote_commit remote_date
    remote_commit=$(git rev-parse "$branch" 2>/dev/null || echo "unknown")
    remote_date=$(git log -1 --format='%cd' --date=short 2>/dev/null || echo "unknown")
    
    echo "$remote_commit|$remote_date"
}

# ============================================
# 克隆源码
# ============================================
clone_source() {
    log INFO "正在克隆 OpenClaw 官方源码..."
    
    # 创建父目录
    mkdir -p "$(dirname "$OPENCLAW_SOURCE_DIR")"
    
    # 克隆源码
    if git clone "$GITHUB_REPO" "$OPENCLAW_SOURCE_DIR"; then
        log INFO "源码克隆完成"
        return 0
    else
        log ERROR "源码克隆失败"
        return 1
    fi
}

# ============================================
# 更新源码
# ============================================
update_source() {
    log INFO "正在更新源码..."
    
    cd "$OPENCLAW_SOURCE_DIR"
    
    # 获取远程更新
    if git fetch origin 2>/dev/null; then
        local local_commit remote_commit
        local_commit=$(git rev-parse HEAD)
        remote_commit=$(git rev-parse origin/main 2>/dev/null) || remote_commit=$(git rev-parse origin/master 2>/dev/null) || remote_commit=""
        
        if [ -n "$remote_commit" ] && [ "$local_commit" != "$remote_commit" ]; then
            log INFO "检测到新版本，正在更新..."
            
            # 尝试合并更新
            if git pull origin main 2>/dev/null || git pull origin master 2>/dev/null; then
                log INFO "源码更新完成"
            else
                # 如果合并失败，尝试变基
                log WARN "合并冲突，尝试变基..."
                if git rebase origin/main 2>/dev/null || git rebase origin/master 2>/dev/null; then
                    log INFO "源码更新完成（变基）"
                else
                    log WARN "更新失败，保持当前版本"
                fi
            fi
        else
            log INFO "源码已是最新版本"
        fi
    else
        log WARN "无法获取远程更新"
    fi
}

# ============================================
# 验证源码完整性
# ============================================
verify_source() {
    log INFO "验证源码完整性..."
    
    # 检查关键文件
    local required_files=("package.json" "README.md")
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$OPENCLAW_SOURCE_DIR/$file" ]; then
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -eq 0 ]; then
        log INFO "源码验证通过"
        return 0
    else
        log ERROR "源码验证失败，缺少文件: ${missing_files[*]}"
        return 1
    fi
}

# ============================================
# 显示源码状态
# ============================================
show_status() {
    echo ""
    echo "========================================"
    echo "📊 源码状态"
    echo "========================================"
    echo ""
    echo "📁 源码目录: $OPENCLAW_SOURCE_DIR"
    
    if [ -d "$OPENCLAW_SOURCE_DIR" ]; then
        echo "📦 源码状态: 已安装"
        
        if [ -d "$OPENCLAW_SOURCE_DIR/.git" ]; then
            cd "$OPENCLAW_SOURCE_DIR"
            local branch commit_count
            branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
            commit_count=$(git rev-list --count HEAD 2>/dev/null || echo "0")
            
            echo "🌿 当前分支: $branch"
            echo "📝 提交数: $commit_count"
            
            # 检查是否有未提交的更改
            if ! git diff --quiet 2>/dev/null; then
                echo -e "${YELLOW}⚠️  有未提交的更改${NC}"
            fi
            
            # 显示最后更新时间
            local last_update
            last_update=$(git log -1 --format='%cd' --date=short 2>/dev/null || echo "未知")
            echo "🕐 最后更新: $last_update"
        fi
        
        # 显示目录大小
        local size
        size=$(du -sh "$OPENCLAW_SOURCE_DIR" 2>/dev/null | cut -f1)
        echo "💾 目录大小: $size"
    else
        echo "📦 源码状态: 未安装"
    fi
    
    echo ""
}

# ============================================
# 主函数
# ============================================
main() {
    echo ""
    echo "========================================"
    echo "📥 OpenClaw 官方源码同步"
    echo "========================================"
    echo ""
    
    # 检查网络
    if ! check_network; then
        log WARN "无网络连接，无法同步源码"
        
        # 如果源码已存在，显示状态后退出
        if [ -d "$OPENCLAW_SOURCE_DIR" ]; then
            show_status
            exit 0
        else
            log ERROR "无网络连接且源码不存在，无法继续"
            exit 1
        fi
    fi
    
    # 检测源码状态
    local status
    status=$(detect_source_status)
    
    case "$status" in
        not_exists)
            log INFO "未检测到源码，将进行全新安装"
            clone_source
            ;;
        existing_git)
            log INFO "检测到 Git 仓库，将进行更新"
            update_source
            ;;
        existing_manual)
            log WARN "检测到手动安装的源码，尝试转换为 Git 仓库"
            # 备份并重新克隆
            mv "$OPENCLAW_SOURCE_DIR" "${OPENCLAW_SOURCE_DIR}.backup.$(date +%s)"
            clone_source
            ;;
    esac
    
    # 验证源码
    if verify_source; then
        show_status
        echo -e "${GREEN}✅ 源码同步完成！${NC}"
        exit 0
    else
        log ERROR "源码验证失败"
        exit 1
    fi
}

# 运行主函数
main "$@"
