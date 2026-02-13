#!/bin/bash

# OpenClaw macOS 智能部署脚本
# 功能: 自动检测环境 + 完整备份 + 智能安装 + 配置启动服务
# 位置: ~/.openclaw/workspace/deploy/mac.sh
# 运行: chmod +x mac.sh && ./mac.sh [--skip-backup] [--force]

set -euo pipefail

# ============================================
# 颜色定义
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================
# 配置
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${HOME}/.openclaw"
LOG_FILE="${WORKSPACE_DIR}/logs/mac-deploy.log"

# 选项
SKIP_BACKUP=false
FORCE=false

# 解析参数
for arg in "$@"; do
    case "$arg" in
        --skip-backup)
            SKIP_BACKUP=true
            ;;
        --force)
            FORCE=true
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
# 步骤显示
# ============================================
step() {
    local step_num="$1"
    local step_name="$2"
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "  🍎 第 $step_num 步：$step_name"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

# ============================================
# 第 1 步：环境检测
# ============================================
check_environment() {
    step 1 "检测 macOS 环境"
    
    echo "📱 系统信息:"
    echo "   • macOS 版本: $(sw_vers -productVersion)"
    echo "   • 构建版本: $(sw_vers -buildVersion)"
    echo "   • 硬件架构: $(uname -m)"
    echo "   • 主机名: $(hostname)"
    echo ""
    
    echo "🔧 检测必要工具..."
    
    local tools_status=()
    
    # Git
    if command -v git &> /dev/null; then
        echo "   ✓ Git: $(git --version)"
    else
        echo "   ✗ Git: 未安装"
        tools_status+=("git")
    fi
    
    # curl
    if command -v curl &> /dev/null; then
        echo "   ✓ curl: $(curl --version | head -1)"
    else
        echo "   ✗ curl: 未安装"
        tools_status+=("curl")
    fi
    
    # Homebrew
    if command -v brew &> /dev/null; then
        echo "   ✓ Homebrew: $(brew --version | head -1)"
    else
        echo "   ✗ Homebrew: 未安装"
        tools_status+=("brew")
    fi
    
    # Node.js
    if command -v node &> /dev/null; then
        local node_version
        node_version=$(node -v)
        echo "   ✓ Node.js: $node_version"
        
        # 检查版本
        local major_version
        major_version=$(echo "$node_version" | cut -d'.' -f1 | tr -d 'v')
        
        if [ "$major_version" -lt 18 ]; then
            echo "      ⚠️  版本过低，建议升级到 Node.js 18+"
            tools_status+=("node-upgrade")
        fi
    else
        echo "   ✗ Node.js: 未安装"
        tools_status+=("node")
    fi
    
    # Python
    if command -v python3 &> /dev/null; then
        echo "   ✓ Python3: $(python3 --version)"
    else
        echo "   ✗ Python3: 未安装"
        tools_status+=("python3")
    fi
    
    echo ""
    
    if [ ${#tools_status[@]} -gt 0 ]; then
        log WARN "需要安装: ${tools_status[*]}"
    else
        log INFO "环境检测通过"
    fi
    
    return 0
}

# ============================================
# 第 2 步：安装依赖
# ============================================
install_dependencies() {
    step 2 "安装 macOS 依赖"
    
    # 安装 Homebrew（如需要）
    if ! command -v brew &> /dev/null; then
        log INFO "安装 Homebrew..."
        echo "📦 正在安装 Homebrew..."
        echo ""
        
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加到 PATH
        if [ -f "/opt/homebrew/bin/brew" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        fi
        
        log INFO "Homebrew 安装完成"
    fi
    
    # 更新 Homebrew
    log INFO "更新 Homebrew..."
    brew update
    
    # 安装必要工具
    local install_list=("git" "curl" "node@20" "python3")
    
    log INFO "安装系统工具: ${install_list[*]}"
    brew install "${install_list[@]}" 2>/dev/null || brew install "${install_list[@]}" --force
    
    # 链接 Node.js
    if [ -f "/usr/local/opt/node@20/bin/node" ] || [ -f "/opt/homebrew/opt/node@20/bin/node" ]; then
        brew link node@20 --force 2>/dev/null || true
    fi
    
    # 验证安装
    echo ""
    echo "📋 验证安装:"
    echo "   • Git: $(git --version)"
    echo "   • Node: $(node -v)"
    echo "   • npm: $(npm -v)"
    echo "   • Python3: $(python3 --version)"
    
    log INFO "依赖安装完成"
}

# ============================================
# 第 3 步：备份现有数据
# ============================================
backup_existing() {
    if [ "$SKIP_BACKUP" = true ]; then
        log INFO "跳过备份步骤"
        return
    fi
    
    step 3 "备份现有数据"
    
    if [ ! -d "$WORKSPACE_DIR" ]; then
        log INFO "OpenClaw 目录不存在，无需备份"
        return
    fi
    
    local file_count
    file_count=$(find "$WORKSPACE_DIR" -type f 2>/dev/null | wc -l)
    
    if [ "$file_count" -eq 0 ]; then
        log INFO "目录为空，无需备份"
        return
    fi
    
    log INFO "备份现有数据..."
    
    local backup_dir="${HOME}/openclaw-macos-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 复制所有内容
    cp -r "$WORKSPACE_DIR"/* "$backup_dir/" 2>/dev/null || true
    
    # 备份信息
    cat > "$backup_dir/backup-info.txt" << EOF
macOS 部署前备份
================
备份时间: $(date)
原始目录: $WORKSPACE_DIR
文件数量: $file_count

恢复命令:
cp -r $backup_dir/* $WORKSPACE_DIR/
EOF
    
    local backup_size
    backup_size=$(du -sh "$backup_dir" | cut -f1)
    log INFO "备份完成: $backup_dir ($backup_size)"
    echo ""
    echo "💡 如需恢复: cp -r $backup_dir/* $WORKSPACE_DIR/"
}

# ============================================
# 第 4 步：同步 GitHub 仓库
# ============================================
sync_github() {
    step 4 "同步 GitHub 仓库"
    
    local repo_dir="${HOME}/--botbot"
    
    if [ -d "$repo_dir/.git" ]; then
        log INFO "更新 GitHub 仓库..."
        cd "$repo_dir"
        
        # 保存本地更改
        if ! git diff --quiet; then
            log WARN "检测到本地更改，暂存..."
            git stash
        fi
        
        # 拉取更新
        if git pull origin main 2>/dev/null; then
            log INFO "仓库已更新"
        elif git pull origin master 2>/dev/null; then
            log INFO "仓库已更新"
        else
            log WARN "拉取失败，保持当前版本"
        fi
        
        # 恢复本地更改
        if git stash list | grep -q .; then
            git stash pop 2>/dev/null || true
        fi
    else
        log INFO "克隆 GitHub 仓库..."
        
        if [ -d "$repo_dir" ]; then
            mv "$repo_dir" "${repo_dir}.old.$(date +%s)"
        fi
        
        git clone https://github.com/Manstein17/--botbot.git "$repo_dir"
        log INFO "仓库克隆完成"
    fi
    
    echo ""
    echo "📁 仓库位置: $repo_dir"
}

# ============================================
# 第 5 步：恢复配置和数据
# ============================================
restore_data() {
    step 5 "恢复配置和数据"
    
    mkdir -p "$WORKSPACE_DIR"
    
    local repo_dir="${HOME}/--botbot"
    
    # 查找备份
    local backup_dir=""
    backup_dir=$(ls -td "${HOME}/OpenClaw-Backups"/backup-* 2>/dev/null | head -1)
    
    if [ -z "$backup_dir" ]; then
        backup_dir=$(ls -td "${HOME}"/openclaw-*-backup-* 2>/dev/null | head -1)
    fi
    
    # 恢复配置
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        echo "📦 发现备份: $backup_dir"
        
        # 配置文件
        if [ -f "$backup_dir/openclaw/openclaw-config.json" ]; then
            cp "$backup_dir/openclaw/openclaw-config.json" "$WORKSPACE_DIR/"
            echo "   ✓ 配置文件"
        fi
        
        if [ -f "$backup_dir/openclaw/openclaw.json" ]; then
            cp "$backup_dir/openclaw/openclaw.json" "$WORKSPACE_DIR/"
            echo "   ✓ 主配置"
        fi
        
        # 目录
        for dir in workspace memory credentials scripts skills; do
            if [ -d "$backup_dir/openclaw/$dir" ]; then
                cp -r "$backup_dir/openclaw/$dir" "$WORKSPACE_DIR/"
                echo "   ✓ $dir"
            fi
        done
        
        log INFO "从备份恢复完成"
    else
        log INFO "使用 GitHub 仓库配置"
        
        # 从仓库复制
        if [ -f "$repo_dir/openclaw-config.json" ]; then
            cp "$repo_dir/openclaw-config.json" "$WORKSPACE_DIR/"
            echo "   ✓ 配置文件"
        fi
        
        for file in AGENTS.md SOUL.md TOOLS.md USER.md HEARTBEAT.md; do
            if [ -f "$repo_dir/$file" ]; then
                mkdir -p "$WORKSPACE_DIR/workspace"
                cp "$repo_dir/$file" "$WORKSPACE_DIR/workspace/"
                echo "   ✓ $file"
            fi
        done
    fi
    
    # 复制部署脚本
    if [ -d "$repo_dir/deploy" ]; then
        mkdir -p "$WORKSPACE_DIR/deploy"
        cp -r "$repo_dir/deploy"/* "$WORKSPACE_DIR/deploy/" 2>/dev/null || true
        echo "   ✓ 部署脚本"
    fi
    
    log INFO "数据恢复完成"
}

# ============================================
# 第 6 步：同步 OpenClaw 源码
# ============================================
sync_official_source() {
    step 6 "同步 OpenClaw 官方源码"
    
    if [ -f "${SCRIPT_DIR}/backup/sync-official-source.sh" ]; then
        bash "${SCRIPT_DIR}/backup/sync-official-source.sh"
    else
        log WARN "同步脚本不存在"
        
        # 手动同步
        local source_dir="${WORKSPACE_DIR}/openclaw-source"
        
        if [ -d "$source_dir/.git" ]; then
            cd "$source_dir"
            git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || log WARN "拉取失败"
        else
            log INFO "克隆 OpenClaw 源码..."
            mkdir -p "$(dirname "$source_dir")"
            git clone https://github.com/openclaw/openclaw.git "$source_dir"
        fi
    fi
}

# ============================================
# 第 7 步：配置 LaunchAgent
# ============================================
configure_launch_agent() {
    step 7 "配置 macOS 启动服务"
    
    local plist_dir="${HOME}/Library/LaunchAgents"
    local plist_file="${plist_dir}/com.openclaw.gateway.plist"
    
    mkdir -p "$plist_dir"
    
    # 检测 openclaw 命令位置
    local openclaw_cmd=""
    
    if command -v openclaw &> /dev/null; then
        openclaw_cmd=$(command -v openclaw)
    elif [ -f "/usr/local/bin/openclaw" ]; then
        openclaw_cmd="/usr/local/bin/openclaw"
    elif [ -f "/opt/homebrew/bin/openclaw" ]; then
        openclaw_cmd="/opt/homebrew/bin/openclaw"
    else
        openclaw_cmd="/usr/local/bin/openclaw"
    fi
    
    # 创建 LaunchAgent
    cat > "$plist_file" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>${openclaw_cmd}</string>
        <string>gateway</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw.error.log</string>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
EOF
    
    echo "   ✓ LaunchAgent: $plist_file"
    echo ""
    echo "💡 启动服务:"
    echo "   launchctl load $plist_file"
    echo ""
    echo "💡 停止服务:"
    echo "   launchctl unload $plist_file"
    
    log INFO "LaunchAgent 配置完成"
}

# ============================================
# 第 8 步：安装 OpenClaw CLI
# ============================================
install_openclaw_cli() {
    step 8 "安装 OpenClaw CLI"
    
    if command -v openclaw &> /dev/null; then
        local current_version
        current_version=$(openclaw --version 2>/dev/null || echo "unknown")
        echo "   ✓ OpenClaw 已安装: $current_version"
        return
    fi
    
    log INFO "安装 OpenClaw CLI..."
    
    # 使用 npm 安装
    if command -v npm &> /dev/null; then
        npm install -g openclaw
        
        # 验证安装
        if command -v openclaw &> /dev/null; then
            echo "   ✓ OpenClaw CLI 安装成功: $(openclaw --version)"
            log INFO "OpenClaw CLI 安装完成"
        else
            log ERROR "安装失败，请手动运行: npm install -g openclaw"
        fi
    else
        log ERROR "npm 未安装"
    fi
}

# ============================================
# 第 9 步：启动 OpenClaw
# ============================================
start_openclaw() {
    step 9 "启动 OpenClaw"
    
    if ! command -v openclaw &> /dev/null; then
        log WARN "openclaw 命令不可用，跳过启动"
        return
    fi
    
    echo ""
    echo -n "是否现在启动 OpenClaw? (Y/n): "
    read -r confirm
    
    if [[ $confirm =~ ^[Nn]$ ]]; then
        log INFO "用户取消启动"
        return
    fi
    
    log INFO "启动 OpenClaw Gateway..."
    
    if openclaw gateway start 2>/dev/null; then
        log INFO "OpenClaw 已启动"
        
        # 等待几秒后检查状态
        sleep 2
        
        if openclaw gateway status 2>/dev/null; then
            :
        fi
    else
        log WARN "启动命令执行失败，请手动运行: openclaw gateway start"
    fi
}

# ============================================
# 显示摘要
# ============================================
show_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ macOS 部署完成                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    echo "📍 目录位置:"
    echo "   • 工作区: $WORKSPACE_DIR"
    echo "   • GitHub: ${HOME}/--botbot"
    echo "   • 源码: ${WORKSPACE_DIR}/openclaw-source"
    echo ""
    
    echo "📋 常用命令:"
    echo "   • 启动: openclaw gateway start"
    echo "   • 停止: openclaw gateway stop"
    echo "   • 状态: openclaw gateway status"
    echo "   • 备份: ${SCRIPT_DIR}/backup/backup-all.sh"
    echo "   • 恢复: ${SCRIPT_DIR}/backup/restore.sh"
    echo ""
    
    echo "📖 文档:"
    echo "   • 详细文档: ${SCRIPT_DIR}/mac-deploy.md"
    echo ""
    
    echo "🔧 故障排查:"
    echo "   • 查看日志: tail -f /tmp/openclaw.log"
    echo "   • 运行诊断: openclaw doctor"
    echo ""
    
    log INFO "macOS 部署任务完成"
}

# ============================================
# 主函数
# ============================================
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║          🍎 OpenClaw macOS 智能部署系统 v2.0                   ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📅 部署时间: $(date)"
    
    # 确认执行
    if [ "$FORCE" = false ]; then
        echo ""
        read -p "确认开始部署? (Y/n): " -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]] && [ -n "$REPLY" ]; then
            echo "取消部署"
            exit 0
        fi
    fi
    
    # 执行各步骤
    check_environment
    install_dependencies
    backup_existing
    sync_github
    restore_data
    sync_official_source
    configure_launch_agent
    install_openclaw_cli
    start_openclaw
    
    # 显示摘要
    show_summary
}

# 运行
main
