#!/bin/bash

# OpenClaw 完整备份脚本
# 功能: 完整备份所有配置、源码、记忆、凭证等
# 位置: ~/.openclaw/workspace/deploy/backup/backup-all.sh
# 运行: chmod +x backup-all.sh && ./backup-all.sh
# 参数: ./backup-all.sh [备份目标位置] [--compress] [--sync-github]

set -euo pipefail

# ============================================
# 颜色定义
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ============================================
# 配置
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${HOME}/.openclaw"
BACKUP_BASE="${1:-${HOME}/OpenClaw-Backups}"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/backup-${TIMESTAMP}"
LOG_FILE="${WORKSPACE_DIR}/logs/backup.log"

# 备份选项
COMPRESS=false
SYNC_GITHUB=false

# 解析参数
for arg in "$@"; do
    case "$arg" in
        --compress)
            COMPRESS=true
            ;;
        --sync-github)
            SYNC_GITHUB=true
            ;;
    esac
done

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
# 备份项目列表
# ============================================
declare -A BACKUP_ITEMS=(
    ["openclaw-config.json"]="OpenClaw 配置文件"
    ["openclaw.json"]="OpenClaw 主配置"
    ["workspace"]="工作区 (AGENTS.md, SOUL.md, memory/, skills/, projects/)"
    ["credentials"]="凭证目录"
    ["scripts"]="自定义脚本"
    ["logs"]="日志目录"
    ["openclaw-source"]="OpenClaw 官方源码"
    ["skills"]="技能目录"
)

# ============================================
# 创建备份目录结构
# ============================================
create_backup_structure() {
    log INFO "创建备份目录..."
    mkdir -p "${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}/openclaw"
    mkdir -p "${BACKUP_DIR}/logs"
}

# ============================================
# 备份单个项目
# ============================================
backup_item() {
    local item="$1"
    local description="$2"
    
    local source_path="${WORKSPACE_DIR}/${item}"
    
    if [ -e "$source_path" ]; then
        log INFO "备份: $description"
        
        # 计算原始大小
        local size_before
        size_before=$(du -sb "$source_path" 2>/dev/null | cut -f1 || echo "0")
        
        # 复制项目
        if [ -d "$source_path" ]; then
            cp -r "$source_path" "${BACKUP_DIR}/openclaw/"
        elif [ -f "$source_path" ]; then
            cp "$source_path" "${BACKUP_DIR}/openclaw/"
        fi
        
        # 验证备份
        if [ -e "${BACKUP_DIR}/openclaw/${item}" ]; then
            local size_after
            size_after=$(du -sb "${BACKUP_DIR}/openclaw/${item}" 2>/dev/null | cut -f1 || echo "0")
            
            if [ "$size_before" -eq "$size_after" ]; then
                log INFO "✓ $description 备份完成"
                return 0
            else
                log WARN "⚠️ $description 大小不匹配 (原: $size_before, 备份: $size_after)"
                return 1
            fi
        fi
    else
        log INFO "跳过: $description (不存在)"
        return 0
    fi
}

# ============================================
# 备份所有项目
# ============================================
backup_all_items() {
    log INFO "开始备份所有项目..."
    echo ""
    
    local success_count=0
    local skip_count=0
    local error_count=0
    
    for item in "${!BACKUP_ITEMS[@]}"; do
        if backup_item "$item" "${BACKUP_ITEMS[$item]}"; then
            ((success_count++)) || true
        else
            ((error_count++)) || true
        fi
    done
    
    echo ""
    log INFO "备份完成: 成功 $success_count, 错误 $error_count"
}

# ============================================
# 备份 GitHub 仓库（如果存在）
# ============================================
backup_github_repo() {
    local github_backup="${BACKUP_DIR}/github-repos"
    
    # 查找常见的 Git 仓库位置
    local repos=(
        "${HOME}/--botbot"
        "${HOME}/openclaw"
        "${HOME}/projects/openclaw"
    )
    
    local found_repo=""
    for repo in "${repos[@]}"; do
        if [ -d "$repo/.git" ]; then
            found_repo="$repo"
            break
        fi
    done
    
    if [ -n "$found_repo" ]; then
        log INFO "备份 GitHub 仓库: $found_repo"
        mkdir -p "$github_backup"
        
        # 只复制源码，不包含 .git 目录（太大）
        cp -r "$found_repo" "$github_backup/" 2>/dev/null || true
        
        # 移除 .git 目录以减小备份大小
        if [ -d "$github_backup/$(basename "$found_repo")/.git" ]; then
            rm -rf "$github_backup/$(basename "$found_repo")/.git"
        fi
        
        log INFO "GitHub 仓库备份完成"
    else
        log INFO "未找到 GitHub 仓库，跳过"
    fi
}

# ============================================
# 创建备份信息文件
# ============================================
create_backup_info() {
    log INFO "创建备份信息文件..."
    
    local total_size
    total_size=$(du -sb "$BACKUP_DIR" 2>/dev/null | cut -f1)
    
    # 转换字节为人类可读格式
    local human_size
    human_size=$(numfmt --to=iec-i --suffix=B "$total_size" 2>/dev/null || echo "${total_size} bytes")
    
    # 统计备份的文件和目录数量
    local file_count dir_count
    file_count=$(find "$BACKUP_DIR" -type f 2>/dev/null | wc -l)
    dir_count=$(find "$BACKUP_DIR" -type d 2>/dev/null | wc -l)
    
    cat > "${BACKUP_DIR}/backup-info.json" << EOF
{
    "backup": {
        "version": "2.0",
        "timestamp": "$(date -Iseconds)",
        "hostname": "$(hostname)",
        "os": "$(uname -s) $(uname -r)",
        "user": "$(whoami)"
    },
    "statistics": {
        "total_size": "$total_size",
        "human_size": "$human_size",
        "file_count": $file_count,
        "directory_count": $dir_count
    },
    "backup_items": $(printf '%s\n' "${!BACKUP_ITEMS[@]}" | jq -R . | jq -s .),
    "restore": {
        "command": "cd ${BACKUP_DIR} && ./deploy/backup/restore.sh",
        "selective_restore": {
            "config": "cp -r ${BACKUP_DIR}/openclaw/openclaw-config.json \${HOME}/.openclaw/",
            "workspace": "cp -r ${BACKUP_DIR}/openclaw/workspace \${HOME}/.openclaw/",
            "memory": "cp -r ${BACKUP_DIR}/openclaw/memory \${HOME}/.openclaw/",
            "credentials": "cp -r ${BACKUP_DIR}/openclaw/credentials \${HOME}/.openclaw/ 2>/dev/null || true",
            "source": "cp -r ${BACKUP_DIR}/openclaw/openclaw-source \${HOME}/.openclaw/"
        }
    }
}
EOF

    # 也创建文本版本的说明
    cat > "${BACKUP_DIR}/backup-info.txt" << EOF
╔════════════════════════════════════════════════════════════════╗
║           OpenClaw 完整备份信息                                 ║
╚════════════════════════════════════════════════════════════════╝

备份时间: $(date)
主机名: $(hostname)
操作系统: $(uname -s) $(uname -r)
用户: $(whoami)

📊 备份统计:
  • 总大小: $human_size
  • 文件数: $file_count
  • 目录数: $dir_count

📦 备份内容:
EOF

    for item in "${!BACKUP_ITEMS[@]}"; do
        local source_path="${WORKSPACE_DIR}/${item}"
        if [ -e "$source_path" ]; then
            local item_size
            item_size=$(du -sh "$source_path" 2>/dev/null | cut -f1 || echo "-")
            echo "  ✓ ${BACKUP_ITEMS[$item]} ($item_size)" >> "${BACKUP_DIR}/backup-info.txt"
        else
            echo "  ○ ${BACKUP_ITEMS[$item]} (不存在)" >> "${BACKUP_DIR}/backup-info.txt"
        fi
    done

    cat >> "${BACKUP_DIR}/backup-info.txt" << EOF

🔧 恢复命令:

# 完整恢复（覆盖现有数据）
cd "${BACKUP_DIR}"
./deploy/backup/restore.sh

# 或手动选择性恢复
cp -r "${BACKUP_DIR}/openclaw/openclaw-config.json" \${HOME}/.openclaw/
cp -r "${BACKUP_DIR}/openclaw/workspace" \${HOME}/.openclaw/
cp -r "${BACKUP_DIR}/openclaw/memory" \${HOME}/.openclaw/ 2>/dev/null || true
cp -r "${BACKUP_DIR}/openclaw/credentials" \${HOME}/.openclaw/ 2>/dev/null || true
cp -r "${BACKUP_DIR}/openclaw/openclaw-source" \${HOME}/.openclaw/ 2>/dev/null || true

💡 提示:
  • 建议定期执行备份
  • 可使用 --compress 选项创建压缩包
  • 可使用 --sync-github 选项同步到 GitHub
EOF

    log INFO "备份信息文件创建完成"
}

# ============================================
# 压缩备份（可选）
# ============================================
compress_backup() {
    if [ "$COMPRESS" = true ]; then
        log INFO "压缩备份文件..."
        
        cd "$(dirname "$BACKUP_DIR")"
        local backup_name
        backup_name=$(basename "$BACKUP_DIR")
        
        # 使用 gzip 压缩
        if tar -czf "${backup_name}.tar.gz" "$backup_name"; then
            log INFO "压缩完成: ${backup_name}.tar.gz"
            
            # 删除原始目录
            rm -rf "$BACKUP_DIR"
            BACKUP_DIR="$(dirname "$BACKUP_DIR")/${backup_name}.tar.gz"
        else
            log ERROR "压缩失败，保持原始备份"
        fi
    fi
}

# ============================================
# 同步到 GitHub（可选）
# ============================================
sync_to_github() {
    if [ "$SYNC_GITHUB" = true ]; then
        log INFO "同步备份到 GitHub..."
        
        # 检查 git 状态
        if [ -d "${HOME}/--botbot/.git" ]; then
            cd "${HOME}/--botbot"
            
            # 添加备份
            git add -A
            
            # 检查是否有更改
            if git diff --cached --quiet; then
                log INFO "没有需要提交的更改"
            else
                git commit -m "Backup: $(date '+%Y-%m-%d %H:%M')"
                
                # 尝试推送
                if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
                    log INFO "备份已同步到 GitHub"
                else
                    log WARN "无法推送到 GitHub，备份仍保存在本地"
                fi
            fi
        else
            log WARN "未找到 GitHub 仓库，跳过同步"
        fi
    fi
}

# ============================================
# 显示备份摘要
# ============================================
show_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    📦 备份完成                                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📍 备份位置: $BACKUP_DIR"
    
    if [ -f "$BACKUP_DIR" ]; then
        # 压缩文件
        local size
        size=$(du -h "$BACKUP_DIR" | cut -f1)
        echo "📊 备份大小: $size"
    elif [ -d "$BACKUP_DIR" ]; then
        local size file_count
        size=$(du -sh "$BACKUP_DIR" | cut -f1)
        file_count=$(find "$BACKUP_DIR" -type f | wc -l)
        echo "📊 备份大小: $size"
        echo "📄 文件数量: $file_count"
    fi
    
    echo ""
    echo "🔧 恢复命令:"
    echo "   cd \"$BACKUP_DIR\""
    echo "   ./deploy/backup/restore.sh"
    echo ""
    echo "💡 提示:"
    echo "   • 建议将备份保存到云盘或外部存储"
    echo "   • 定期执行备份确保数据安全"
    echo ""
}

# ============================================
# 主函数
# ============================================
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              📦 OpenClaw 完整备份系统                          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📅 备份时间: $(date)"
    echo "📁 备份位置: $BACKUP_DIR"
    echo ""
    
    # 创建备份目录
    create_backup_structure
    
    # 备份所有项目
    backup_all_items
    
    # 备份 GitHub 仓库
    backup_github_repo
    
    # 创建备份信息
    create_backup_info
    
    # 压缩备份（如果启用）
    compress_backup
    
    # 同步到 GitHub（如果启用）
    sync_to_github
    
    # 显示摘要
    show_summary
    
    log INFO "备份任务完成"
}

# 运行主函数
main "$@"
