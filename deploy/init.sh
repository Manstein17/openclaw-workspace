#!/bin/bash

# OpenClaw 一键部署初始化脚本
# 功能: 初始化环境、检测依赖、安装配置、恢复备份
# 位置: ~/.openclaw/workspace/deploy/init.sh
# 运行: chmod +x init.sh && ./init.sh [--skip-backup] [--platform PLATFORM]

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
NC='\033[0m'

# ============================================
# 配置
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="${HOME}/.openclaw"
GITHUB_REPO="https://github.com/Manstein17/--botbot.git"
LOG_FILE="${WORKSPACE_DIR}/logs/init.log"

# 选项
SKIP_BACKUP=false
PLATFORM=""
FORCE=false

# ============================================
# 解析参数
# ============================================
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --skip-backup     跳过备份步骤"
            echo "  --platform PLATFORM   指定平台 (macos/linux/windows/cloud/android)"
            echo "  --force           强制执行，跳过确认"
            echo "  --help, -h        显示此帮助"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

# ============================================
# 检测平台
# ============================================
detect_platform() {
    if [ -n "$PLATFORM" ]; then
        echo "$PLATFORM"
        return
    fi
    
    case "$(uname -s)" in
        Darwin*)
            echo "macos"
            ;;
        Linux*)
            # 检查是否是 Android (Termux)
            if [ -f "/data/data/com.termux/files/home/.termux" ] || [ -n "${TERMUX_VERSION:-}" ]; then
                echo "android"
            else
                echo "linux"
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

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
# 显示横幅
# ============================================
show_banner() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                                                                ║"
    echo "║          🤖 OpenClaw 一键部署系统 v2.0                         ║"
    echo "║                                                                ║"
    echo "║          自动检测 • 智能配置 • 一键恢复                         ║"
    echo "║                                                                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# ============================================
# 环境检测
# ============================================
check_environment() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "🔍 第 1 步：检测环境"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    local platform
    platform=$(detect_platform)
    echo "📱 检测平台: $platform"
    
    # 检测系统信息
    case "$platform" in
        macos)
            echo "🍎 操作系统: macOS $(sw_vers -productVersion)"
            echo "💻 硬件: $(uname -m)"
            ;;
        linux)
            echo "🐧 操作系统: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
            echo "💻 内核: $(uname -r)"
            ;;
        windows)
            echo "🪟 操作系统: Windows"
            ;;
        android)
            echo "📱 操作系统: Android (Termux)"
            ;;
    esac
    
    # 检测必要工具
    echo ""
    echo "📦 检测必要工具..."
    
    local required_tools=("git" "curl")
    local optional_tools=("node" "python3" "brew")
    local missing_required=()
    local missing_optional=()
    
    for tool in "${required_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            local version
            version=$("$tool" --version 2>&1 | head -1 || echo "unknown")
            echo -e "  ✓ $tool: $version"
        else
            echo -e "  ✗ $tool: ${RED}未安装${NC}"
            missing_required+=("$tool")
        fi
    done
    
    for tool in "${optional_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            local version
            version=$("$tool" --version 2>&1 | head -1 || echo "unknown")
            echo -e "  ✓ $tool: $version (可选)"
        else
            echo -e "  ○ $tool: 未安装 (可选)"
            missing_optional+=("$tool")
        fi
    done
    
    echo ""
    
    if [ ${#missing_required[@]} -gt 0 ]; then
        log ERROR "缺少必要工具: ${missing_required[*]}"
        log INFO "请先安装缺失的工具后重试"
        exit 1
    fi
    
    # 检测 OpenClaw 目录
    echo ""
    echo "📁 检测 OpenClaw 目录..."
    
    if [ -d "$WORKSPACE_DIR" ]; then
        echo -e "  ✓ OpenClaw 目录已存在: $WORKSPACE_DIR"
        
        local file_count
        file_count=$(find "$WORKSPACE_DIR" -type f 2>/dev/null | wc -l)
        echo -e "  📄 文件数量: $file_count"
    else
        echo -e "  ○ OpenClaw 目录不存在，将创建"
    fi
    
    echo ""
    log INFO "环境检测完成"
}

# ============================================
# 安装依赖
# ============================================
install_dependencies() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "📦 第 2 步：安装依赖"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    local platform
    platform=$(detect_platform)
    
    case "$platform" in
        macos)
            install_dependencies_macos
            ;;
        linux)
            install_dependencies_linux
            ;;
        windows)
            install_dependencies_windows
            ;;
        android)
            install_dependencies_android
            ;;
    esac
    
    echo ""
    log INFO "依赖安装完成"
}

# ============================================
# macOS 依赖安装
# ============================================
install_dependencies_macos() {
    echo "🍎 安装 macOS 依赖..."
    
    # 检查 Homebrew
    if ! command -v brew &> /dev/null; then
        echo "  📦 正在安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # 安装依赖
    echo "  📦 安装系统依赖..."
    brew install git curl node python3
    
    # 检查 Node.js 版本
    if command -v node &> /dev/null; then
        local node_version
        node_version=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        
        if [ "$node_version" -lt 18 ]; then
            echo "  ⚠️  Node.js 版本过低 (v${node_version})，正在更新..."
            brew install node@20
            brew link node@20 --force
        fi
    fi
    
    # 检查 npm
    if command -v npm &> /dev/null; then
        echo "  ✓ npm: $(npm -v)"
    fi
}

# ============================================
# Linux 依赖安装
# ============================================
install_dependencies_linux() {
    echo "🐧 安装 Linux 依赖..."
    
    # 检测包管理器
    local package_manager=""
    local install_cmd=""
    
    if command -v apt-get &> /dev/null; then
        package_manager="apt"
        install_cmd="sudo apt-get install -y"
    elif command -v yum &> /dev/null; then
        package_manager="yum"
        install_cmd="sudo yum install -y"
    elif command -v dnf &> /dev/null; then
        package_manager="dnf"
        install_cmd="sudo dnf install -y"
    elif command -v pacman &> /dev/null; then
        package_manager="pacman"
        install_cmd="sudo pacman -S --noconfirm"
    elif command -v zypper &> /dev/null; then
        package_manager="zypper"
        install_cmd="sudo zypper install -y"
    fi
    
    if [ -z "$package_manager" ]; then
        log WARN "未检测到支持的包管理器，请手动安装依赖"
        return
    fi
    
    echo "  📦 使用 $package_manager 安装依赖..."
    
    # 安装基础依赖
    $install_cmd git curl
    
    # 安装 Node.js
    if ! command -v node &> /dev/null; then
        # 添加 NodeSource 仓库
        if command -v curl &> /dev/null; then
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>/dev/null || true
            $install_cmd nodejs
        fi
    fi
    
    # 安装 Python
    if ! command -v python3 &> /dev/null; then
        $install_cmd python3 python3-pip
    fi
    
    echo "  ✓ 依赖安装完成"
}

# ============================================
# Windows 依赖安装
# ============================================
install_dependencies_windows() {
    echo "🪟 安装 Windows 依赖..."
    echo "  ⚠️  Windows 平台请使用 PowerShell 脚本部署"
    echo "  运行: .\deploy\windows.ps1"
    
    # 检查是否使用 WSL
    if command -v wsl.exe &> /dev/null; then
        echo "  ✓ 检测到 WSL，可使用 Linux 部署方式"
    fi
}

# ============================================
# Android (Termux) 依赖安装
# ============================================
install_dependencies_android() {
    echo "📱 安装 Android (Termux) 依赖..."
    
    # 更新仓库
    echo "  📦 更新包仓库..."
    apt-get update -y 2>/dev/null || true
    
    # 安装基础依赖
    echo "  📦 安装基础依赖..."
    apt-get install -y git curl nodejs python 2>/dev/null || true
    
    echo "  ✓ 依赖安装完成"
}

# ============================================
# 备份现有数据
# ============================================
backup_existing() {
    if [ "$SKIP_BACKUP" = true ]; then
        log INFO "跳过备份步骤"
        return
    fi
    
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "💾 第 3 步：备份现有数据"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    if [ ! -d "$WORKSPACE_DIR" ]; then
        log INFO "OpenClaw 目录不存在，无需备份"
        return
    fi
    
    # 检查是否有内容
    local file_count
    file_count=$(find "$WORKSPACE_DIR" -type f 2>/dev/null | wc -l)
    
    if [ "$file_count" -eq 0 ]; then
        log INFO "OpenClaw 目录为空，无需备份"
        return
    fi
    
    log INFO "备份现有数据..."
    
    local backup_dir="${HOME}/openclaw-backup-preinit-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 复制所有内容
    cp -r "$WORKSPACE_DIR"/* "$backup_dir/" 2>/dev/null || true
    
    # 创建备份信息
    cat > "$backup_dir/backup-info.txt" << EOF
OpenClaw 部署前备份
====================
备份时间: $(date)
原始目录: $WORKSPACE_DIR
文件数量: $file_count

恢复命令:
cp -r $backup_dir/* $WORKSPACE_DIR/
EOF
    
    log INFO "备份完成: $backup_dir"
    echo ""
    echo "  💡 如需恢复，使用: cp -r $backup_dir/* $WORKSPACE_DIR/"
}

# ============================================
# 克隆/更新 GitHub 仓库
# ============================================
sync_github_repo() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "📥 第 4 步：同步 GitHub 仓库"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    local repo_dir="${HOME}/--botbot"
    
    if [ -d "$repo_dir/.git" ]; then
        log INFO "更新 GitHub 仓库..."
        cd "$repo_dir"
        git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || log WARN "拉取失败"
    else
        log INFO "克隆 GitHub 仓库..."
        
        if [ -d "$repo_dir" ]; then
            # 目录存在但不是 git 仓库
            mv "$repo_dir" "${repo_dir}.old.$(date +%s)"
        fi
        
        git clone "$GITHUB_REPO" "$repo_dir"
    fi
    
    log INFO "GitHub 仓库同步完成: $repo_dir"
}

# ============================================
# 恢复配置和数据
# ============================================
restore_data() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "🔄 第 5 步：恢复配置和数据"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    # 确保目标目录存在
    mkdir -p "$WORKSPACE_DIR"
    
    local repo_dir="${HOME}/--botbot"
    
    # 检查是否有备份可以恢复
    local backup_dir=""
    
    # 查找最近的备份
    backup_dir=$(ls -td "${HOME}/OpenClaw-Backups"/backup-* 2>/dev/null | head -1)
    
    if [ -z "$backup_dir" ]; then
        # 查找部署前备份
        backup_dir=$(ls -td "${HOME}"/openclaw-backup-preinit-* 2>/dev/null | head -1)
    fi
    
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        echo "📦 发现备份: $backup_dir"
        echo -n "是否恢复备份? (Y/n): "
        read -r restore_backup
        
        if [[ ! $restore_backup =~ ^[Nn]$ ]]; then
            log INFO "从备份恢复数据..."
            
            # 恢复配置
            if [ -f "$backup_dir/openclaw/openclaw-config.json" ]; then
                cp "$backup_dir/openclaw/openclaw-config.json" "$WORKSPACE_DIR/"
                echo "  ✓ 配置文件"
            fi
            
            if [ -f "$backup_dir/openclaw/openclaw.json" ]; then
                cp "$backup_dir/openclaw/openclaw.json" "$WORKSPACE_DIR/"
                echo "  ✓ 主配置"
            fi
            
            # 恢复工作区
            if [ -d "$backup_dir/openclaw/workspace" ]; then
                cp -r "$backup_dir/openclaw/workspace" "$WORKSPACE_DIR/"
                echo "  ✓ 工作区"
            fi
            
            # 恢复记忆
            if [ -d "$backup_dir/openclaw/memory" ]; then
                cp -r "$backup_dir/openclaw/memory" "$WORKSPACE_DIR/"
                echo "  ✓ 记忆"
            fi
            
            # 恢复其他目录
            for dir in credentials scripts skills; do
                if [ -d "$backup_dir/openclaw/$dir" ]; then
                    cp -r "$backup_dir/openclaw/$dir" "$WORKSPACE_DIR/"
                    echo "  ✓ $dir"
                fi
            done
            
            log INFO "备份恢复完成"
        fi
    else
        log INFO "未找到备份，将使用 GitHub 仓库配置"
        
        # 从 GitHub 仓库复制配置
        if [ -f "$repo_dir/openclaw-config.json" ]; then
            cp "$repo_dir/openclaw-config.json" "$WORKSPACE_DIR/"
            echo "  ✓ 从仓库复制配置文件"
        fi
        
        if [ -f "$repo_dir/AGENTS.md" ]; then
            mkdir -p "$WORKSPACE_DIR/workspace"
            cp "$repo_dir/AGENTS.md" "$WORKSPACE_DIR/workspace/"
            echo "  ✓ 从仓库复制 AGENTS.md"
        fi
    fi
    
    # 复制部署脚本
    if [ -d "$repo_dir/deploy" ]; then
        mkdir -p "$WORKSPACE_DIR/deploy"
        cp -r "$repo_dir/deploy"/* "$WORKSPACE_DIR/deploy/"
        echo "  ✓ 部署脚本"
    fi
    
    echo ""
    log INFO "数据恢复完成"
}

# ============================================
# 同步官方源码
# ============================================
sync_official_source() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "📥 第 6 步：同步 OpenClaw 官方源码"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    if [ -f "${SCRIPT_DIR}/backup/sync-official-source.sh" ]; then
        bash "${SCRIPT_DIR}/backup/sync-official-source.sh"
    else
        log WARN "同步脚本不存在，跳过"
    fi
}

# ============================================
# 配置启动服务
# ============================================
configure_service() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "⚙️  第 7 步：配置启动服务"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    local platform
    platform=$(detect_platform)
    
    case "$platform" in
        macos)
            configure_launch_agent
            ;;
        linux)
            configure_systemd
            ;;
        android)
            configure_termux_boot
            ;;
    esac
    
    echo ""
    log INFO "启动服务配置完成"
}

# ============================================
# 配置 macOS LaunchAgent
# ============================================
configure_launch_agent() {
    echo "🍎 配置 macOS LaunchAgent..."
    
    local plist_dir="${HOME}/Library/LaunchAgents"
    local plist_file="${plist_dir}/com.openclaw.gateway.plist"
    
    mkdir -p "$plist_dir"
    
    # 创建 LaunchAgent 配置
    cat > "$plist_file" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/openclaw</string>
        <string>gateway</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw.error.log</string>
</dict>
</plist>
EOF
    
    echo "  ✓ LaunchAgent 配置已创建: $plist_file"
    echo "  💡 启动: launchctl load $plist_file"
}

# ============================================
# 配置 Linux systemd
# ============================================
configure_systemd() {
    echo "🐧 配置 systemd 服务..."
    
    # 检查是否有 systemd
    if ! command -v systemctl &> /dev/null; then
        echo "  ⚠️  未检测到 systemd，跳过"
        return
    fi
    
    local service_file="/etc/systemd/system/openclaw-gateway.service"
    
    # 检查权限
    if [ "$(id -u)" -ne 0 ]; then
        echo "  ⚠️  需要 root 权限创建 systemd 服务"
        echo "  请手动运行: sudo cp openclaw-gateway.service /etc/systemd/system/"
        return
    fi
    
    # 创建服务文件
    cat > "$service_file" << 'EOF'
[Unit]
Description=OpenClaw Gateway Service
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=%h/.openclaw
ExecStart=/usr/local/bin/openclaw gateway start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    echo "  ✓ systemd 服务已创建: $service_file"
    echo "  💡 启动: sudo systemctl enable openclaw-gateway"
}

# ============================================
# 配置 Termux 启动
# ============================================
configure_termux_boot() {
    echo "📱 配置 Termux 启动..."
    
    local termux_autostart="${HOME}/.termux/boot"
    mkdir -p "$termux_autostart"
    
    # 创建启动脚本
    cat > "${termux_autostart}/openclaw" << 'EOF'
#!/data/data/com.termux/files/usr/bin/sh
# OpenClaw 自动启动脚本

# 启动 OpenClaw Gateway
openclaw gateway start
EOF
    
    chmod +x "${termux_autostart}/openclaw"
    echo "  ✓ Termux 启动脚本已创建"
}

# ============================================
# 启动 OpenClaw
# ============================================
start_openclaw() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo "🚀 第 8 步：启动 OpenClaw"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    # 检查 openclaw 命令
    if ! command -v openclaw &> /dev/null; then
        log WARN "openclaw 命令未找到"
        echo ""
        echo "  请先安装 OpenClaw CLI:"
        echo "    npm install -g openclaw"
        echo ""
        echo "  或使用 npx:"
        echo "    npx openclaw gateway start"
        echo ""
        return
    fi
    
    echo -n "是否现在启动 OpenClaw? (Y/n): "
    read -r start_now
    
    if [[ ! $start_now =~ ^[Nn]$ ]]; then
        log INFO "启动 OpenClaw Gateway..."
        
        if openclaw gateway start 2>/dev/null; then
            log INFO "OpenClaw 已启动"
        else
            log WARN "启动失败，请手动运行: openclaw gateway start"
        fi
    fi
}

# ============================================
# 显示摘要
# ============================================
show_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ 初始化完成                                 ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    local platform
    platform=$(detect_platform)
    
    echo "📍 目录位置:"
    echo "   • 工作区: $WORKSPACE_DIR"
    echo "   • GitHub: ${HOME}/--botbot"
    echo "   • 备份: ${HOME}/OpenClaw-Backups"
    echo ""
    
    echo "📋 常用命令:"
    echo "   • 启动: openclaw gateway start"
    echo "   • 停止: openclaw gateway stop"
    echo "   • 状态: openclaw gateway status"
    echo "   • 备份: ${SCRIPT_DIR}/backup/backup-all.sh"
    echo "   • 恢复: ${SCRIPT_DIR}/backup/restore.sh"
    echo ""
    
    echo "📖 后续操作:"
    echo "   1. 安装 OpenClaw CLI: npm install -g openclaw"
    echo "   2. 启动服务: openclaw gateway start"
    echo "   3. 查看状态: openclaw gateway status"
    echo ""
    
    echo "💡 提示:"
    echo "   • 遇到问题请查看日志: $LOG_FILE"
    echo "   • 使用 --help 查看更多选项"
    echo ""
}

# ============================================
# 主函数
# ============================================
main() {
    # 显示横幅
    show_banner
    
    # 确认执行
    if [ "$FORCE" = false ]; then
        echo "此脚本将执行以下操作:"
        echo "  1. 检测系统环境"
        echo "  2. 安装必要依赖"
        echo "  3. 备份现有数据"
        echo "  4. 同步 GitHub 仓库"
        echo "  5. 恢复配置和数据"
        echo "  6. 同步 OpenClaw 源码"
        echo "  7. 配置启动服务"
        echo "  8. 启动 OpenClaw"
        echo ""
        
        read -p "确认继续? (Y/n): " -n 1 -r
        echo ""
        
        if [[ ! $REPLY =~ ^[Yy]$ ]] && [ -n "$REPLY" ]; then
            echo "取消执行"
            exit 0
        fi
    fi
    
    # 执行各步骤
    check_environment
    install_dependencies
    backup_existing
    sync_github_repo
    restore_data
    sync_official_source
    configure_service
    start_openclaw
    
    # 显示摘要
    show_summary
    
    log INFO "初始化任务完成"
}

# 运行主函数
main
