#!/bin/bash

# OpenClaw 一键恢复脚本
# 功能: 从备份恢复所有配置、源码、记忆等
# 位置: ~/.openclaw/workspace/deploy/backup/restore.sh
# 运行: chmod +x restore.sh && ./restore.sh [备份目录]
# 参数: 
#   ./restore.sh                    # 从默认备份目录选择
#   ./restore.sh /path/to/backup   # 从指定目录恢复

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
WORKSPACE_DIR="${HOME}/.openclaw"
BACKUP_BASE="${HOME}/OpenClaw-Backups"
LOG_FILE="${WORKSPACE_DIR}/logs/restore.log"

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
# 显示警告
# ============================================
show_warning() {
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                    ⚠️  重要警告                                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}此操作将恢复备份数据到您的系统，可能会覆盖现有文件。${NC}"
    echo ""
    echo "📋 恢复操作包括:"
    echo "  1. 恢复 OpenClaw 配置文件"
    echo "  2. 恢复工作区 (workspace/)"
    echo "  3. 恢复记忆 (memory/)"
    echo "  4. 恢复凭证 (credentials/)"
    echo "  5. 恢复源码 (openclaw-source/)"
    echo ""
    
    read -p "确认继续? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log INFO "用户取消恢复操作"
        exit 0
    fi
}

# ============================================
# 查找备份目录
# ============================================
find_backup_directory() {
    local backup_dir="$1"
    
    # 如果指定了目录
    if [ -n "$backup_dir" ] && [ -e "$backup_dir" ]; then
        echo "$backup_dir"
        return 0
    fi
    
    # 查找最新的备份
    local latest_backup
    latest_backup=$(ls -td "${BACKUP_BASE}"/backup-* 2>/dev/null | head -1)
    
    if [ -n "$latest_backup" ]; then
        echo "$latest_backup"
        return 0
    fi
    
    # 查找压缩的备份
    local latest_compressed
    latest_compressed=$(ls -t "${BACKUP_BASE}"/*.tar.gz 2>/dev/null | head -1)
    
    if [ -n "$latest_compressed" ]; then
        echo "$latest_compressed"
        return 0
    fi
    
    return 1
}

# ============================================
# 选择备份目录
# ============================================
select_backup_directory() {
    echo ""
    echo "📂 可用的备份:"
    echo ""
    
    local backups=()
    local index=1
    
    # 列出目录备份
    for backup in "${BACKUP_BASE}"/backup-*/; do
        if [ -d "$backup" ]; then
            local size date
            size=$(du -sh "$backup" 2>/dev/null | cut -f1)
            date=$(basename "$backup" | sed 's/backup-//')
            echo "  [$index] $(basename "$backup") - $size ($date)"
            backups+=("$backup")
            ((index++))
        fi
    done
    
    # 列出压缩备份
    for backup in "${BACKUP_BASE}"/*.tar.gz; do
        if [ -f "$backup" ]; then
            local size date
            size=$(du -h "$backup" 2>/dev/null | cut -f1)
            date=$(basename "$backup" | sed 's/backup-\(.*\)\.tar.gz/\1/')
            echo "  [$index] $(basename "$backup") - $size ($date)"
            backups+=("$backup")
            ((index++))
        fi
    done
    
    if [ ${#backups[@]} -eq 0 ]; then
        log ERROR "未找到任何备份"
        exit 1
    fi
    
    echo ""
    echo -n "请选择备份 (1-${#backups[@]}, 默认 1): "
    read -r selection
    
    if [ -z "$selection" ]; then
        selection=1
    fi
    
    if [ "$selection" -ge 1 ] && [ "$selection" -le ${#backups[@]} ]; then
        echo "${backups[$((selection-1))]}"
    else
        log ERROR "无效选择"
        exit 1
    fi
}

# ============================================
# 解压压缩的备份
# ============================================
extract_backup() {
    local backup_path="$1"
    
    # 检查是否是压缩文件
    if [[ "$backup_path" == *.tar.gz ]]; then
        log INFO "解压备份文件..."
        
        local extract_dir="${BACKUP_BASE}/temp-extract-$(date +%s)"
        mkdir -p "$extract_dir"
        
        if tar -xzf "$backup_path" -C "$extract_dir"; then
            # 找到解压后的目录
            local extracted
            extracted=$(ls -d "${extract_dir}"/backup-*/ 2>/dev/null | head -1)
            
            if [ -n "$extracted" ]; then
                echo "$extracted"
            else
                log ERROR "解压失败，无法找到备份内容"
                exit 1
            fi
        else
            log ERROR "解压失败"
            exit 1
        fi
    else
        echo "$backup_path"
    fi
}

# ============================================
# 验证备份完整性
# ============================================
verify_backup() {
    local backup_dir="$1"
    
    log INFO "验证备份完整性..."
    
    # 检查必要文件
    if [ ! -d "$backup_dir/openclaw" ]; then
        log ERROR "备份目录结构无效: 缺少 openclaw 目录"
        return 1
    fi
    
    # 检查备份信息
    if [ -f "$backup_dir/backup-info.txt" ]; then
        log INFO "找到备份信息文件"
        cat "$backup_dir/backup-info.txt"
    fi
    
    # 列出备份内容
    echo ""
    echo "📦 备份内容:"
    ls -la "$backup_dir/openclaw/" 2>/dev/null || true
    
    return 0
}

# ============================================
# 备份现有数据（恢复前）
# ============================================
backup_existing_data() {
    log INFO "备份现有数据..."
    
    local pre_restore_dir="${WORKSPACE_DIR}/pre-restore-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$pre_restore_dir"
    
    # 备份现有配置
    if [ -d "$WORKSPACE_DIR" ]; then
        cp -r "$WORKSPACE_DIR"/* "$pre_restore_dir/" 2>/dev/null || true
        log INFO "现有数据已备份到: $pre_restore_dir"
    fi
}

# ============================================
# 恢复单个项目
# ============================================
restore_item() {
    local source="$1"
    local destination="$2"
    local description="$3"
    
    if [ -e "$source" ]; then
        log INFO "恢复: $description"
        
        # 创建目标目录
        mkdir -p "$(dirname "$destination")"
        
        # 复制文件
        if [ -d "$source" ]; then
            cp -rf "$source" "$destination"
        else
            cp -f "$source" "$destination"
        fi
        
        # 验证
        if [ -e "$destination" ]; then
            log INFO "✓ $description 恢复完成"
            return 0
        else
            log ERROR "✗ $description 恢复失败"
            return 1
        fi
    else
        log INFO "跳过: $description (备份中不存在)"
        return 0
    fi
}

# ============================================
# 恢复所有项目
# ============================================
restore_all_items() {
    local backup_dir="$1"
    
    echo ""
    log INFO "开始恢复数据..."
    echo ""
    
    # 确保目标目录存在
    mkdir -p "$WORKSPACE_DIR"
    
    # 恢复配置文件
    restore_item \
        "$backup_dir/openclaw/openclaw-config.json" \
        "$WORKSPACE_DIR/openclaw-config.json" \
        "OpenClaw 配置文件"
    
    restore_item \
        "$backup_dir/openclaw/openclaw.json" \
        "$WORKSPACE_DIR/openclaw.json" \
        "OpenClaw 主配置"
    
    # 恢复工作区
    restore_item \
        "$backup_dir/openclaw/workspace" \
        "$WORKSPACE_DIR/workspace" \
        "工作区 (workspace)"
    
    # 恢复记忆
    restore_item \
        "$backup_dir/openclaw/memory" \
        "$WORKSPACE_DIR/memory" \
        "记忆 (memory)"
    
    # 恢复凭证（可选）
    restore_item \
        "$backup_dir/openclaw/credentials" \
        "$WORKSPACE_DIR/credentials" \
        "凭证 (credentials)"
    
    # 恢复自定义脚本
    restore_item \
        "$backup_dir/openclaw/scripts" \
        "$WORKSPACE_DIR/scripts" \
        "自定义脚本 (scripts)"
    
    # 恢复日志
    restore_item \
        "$backup_dir/openclaw/logs" \
        "$WORKSPACE_DIR/logs" \
        "日志 (logs)"
    
    # 恢复源码
    restore_item \
        "$backup_dir/openclaw/openclaw-source" \
        "$WORKSPACE_DIR/openclaw-source" \
        "OpenClaw 官方源码"
    
    # 恢复技能
    restore_item \
        "$backup_dir/openclaw/skills" \
        "$WORKSPACE_DIR/skills" \
        "技能 (skills)"
    
    echo ""
}

# ============================================
# 设置权限
# ============================================
set_permissions() {
    log INFO "设置文件权限..."
    
    # 设置工作区目录权限
    if [ -d "$WORKSPACE_DIR" ]; then
        chmod -R 700 "$WORKSPACE_DIR" 2>/dev/null || true
        
        # 设置关键文件权限
        chmod 600 "$WORKSPACE_DIR/openclaw-config.json" 2>/dev/null || true
        chmod 600 "$WORKSPACE_DIR/openclaw.json" 2>/dev/null || true
        
        # 设置凭证目录权限（如果存在）
        if [ -d "$WORKSPACE_DIR/credentials" ]; then
            chmod -R 600 "$WORKSPACE_DIR/credentials" 2>/dev/null || true
        fi
        
        log INFO "权限设置完成"
    fi
}

# ============================================
# 验证恢复结果
# ============================================
verify_restore() {
    log INFO "验证恢复结果..."
    
    echo ""
    echo "📊 恢复后的目录结构:"
    echo ""
    
    local items=(
        "openclaw-config.json:配置文件"
        "openclaw.json:主配置"
        "workspace:工作区"
        "memory:记忆"
        "credentials:凭证"
        "scripts:脚本"
        "logs:日志"
        "openclaw-source:源码"
        "skills:技能"
    )
    
    local restored_count=0
    
    for item in "${items[@]}"; do
        local name="${item%%:*}"
        local desc="${item##*:}"
        
        if [ -e "$WORKSPACE_DIR/$name" ]; then
            local size
            size=$(du -sh "$WORKSPACE_DIR/$name" 2>/dev/null | cut -f1 || echo "-")
            echo -e "  ${GREEN}✓${NC} $desc ($size)"
            ((restored_count++)) || true
        else
            echo -e "  ${YELLOW}○${NC} $desc (不存在)"
        fi
    done
    
    echo ""
    log INFO "恢复完成: $restored_count/9 项"
}

# ============================================
# 显示恢复摘要
# ============================================
show_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ 恢复完成                                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📍 恢复位置: $WORKSPACE_DIR"
    echo ""
    echo "🔧 后续操作:"
    echo "   • 启动 OpenClaw: openclaw gateway start"
    echo "   • 查看状态: openclaw gateway status"
    echo "   • 运行测试: openclaw doctor"
    echo ""
    echo "💡 提示:"
    echo "   • 如果遇到问题，备份的原始数据保存在:"
    echo "     ${HOME}/.openclaw/pre-restore-*"
    echo "   • 可以使用该目录手动恢复"
    echo ""
}

# ============================================
# 选择性恢复
# ============================================
selective_restore() {
    local backup_dir="$1"
    
    echo ""
    echo "📋 选择性恢复"
    echo "============="
    echo ""
    echo "  1. 完整恢复 (所有文件)"
    echo "  2. 仅恢复配置文件"
    echo "  3. 仅恢复工作区"
    echo "  4. 仅恢复记忆"
    echo "  5. 仅恢复源码"
    echo "  6. 退出"
    echo ""
    echo -n "请选择 [1-6]: "
    read -r selection
    
    case "$selection" in
        1)
            # 完整恢复在主流程中处理
            return 0
            ;;
        2)
            restore_item "$backup_dir/openclaw/openclaw-config.json" "$WORKSPACE_DIR/openclaw-config.json" "配置文件"
            restore_item "$backup_dir/openclaw/openclaw.json" "$WORKSPACE_DIR/openclaw.json" "主配置"
            ;;
        3)
            restore_item "$backup_dir/openclaw/workspace" "$WORKSPACE_DIR/workspace" "工作区"
            ;;
        4)
            restore_item "$backup_dir/openclaw/memory" "$WORKSPACE_DIR/memory" "记忆"
            ;;
        5)
            restore_item "$backup_dir/openclaw/openclaw-source" "$WORKSPACE_DIR/openclaw-source" "源码"
            ;;
        6)
            log INFO "取消恢复"
            exit 0
            ;;
        *)
            log ERROR "无效选择"
            exit 1
            ;;
    esac
}

# ============================================
# 主函数
# ============================================
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              🔄 OpenClaw 一键恢复系统                            ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # 查找备份目录
    local backup_dir
    if [ -n "${1:-}" ]; then
        backup_dir=$(find_backup_directory "$1")
    else
        backup_dir=$(select_backup_directory)
    fi
    
    if [ -z "$backup_dir" ]; then
        log ERROR "未找到备份目录"
        exit 1
    fi
    
    # 显示备份信息
    echo ""
    echo "📦 选中的备份: $backup_dir"
    
    # 检查是否是压缩文件，如果是则解压
    if [[ "$backup_dir" == *.tar.gz ]]; then
        backup_dir=$(extract_backup "$backup_dir")
        echo "📦 解压后: $backup_dir"
    fi
    
    # 验证备份
    if ! verify_backup "$backup_dir"; then
        log ERROR "备份验证失败"
        exit 1
    fi
    
    # 显示警告
    show_warning
    
    # 备份现有数据
    backup_existing_data
    
    # 询问是否选择性恢复
    echo ""
    echo -n "是否进行选择性恢复? (y/N): "
    read -r selective
    
    if [[ $selective =~ ^[Yy]$ ]]; then
        selective_restore "$backup_dir"
    else
        # 完整恢复
        restore_all_items "$backup_dir"
    fi
    
    # 设置权限
    set_permissions
    
    # 验证恢复结果
    verify_restore
    
    # 显示摘要
    show_summary
    
    log INFO "恢复任务完成"
}

# 运行主函数
main "$@"
