# OpenClaw Windows 部署脚本
# 运行方式: 右键以管理员身份运行 PowerShell，然后执行 .\windows.ps1
# 功能: 一键部署 + 自动同步官方源码 + 完整备份

$ErrorActionPreference = "Stop"

# 颜色函数
function Write-Green { param($text) Write-Host $text -ForegroundColor Green }
function Write-Yellow { param($text) Write-Host $text -ForegroundColor Yellow }
function Write-Blue { param($text) Write-Host $text -ForegroundColor Cyan }
function Write-Red { param($text) Write-Host $text -ForegroundColor Red }

Write-Host "🪟 欢迎使用 OpenClaw Windows 部署脚本！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# ============================================
# 第 1 部分：完整备份（部署前必做）
# ============================================
Write-Yellow "📦 第 1 步：备份现有数据..."

$backupDir = "$env:USERPROFILE\openclaw-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# 备份 $HOME\.openclaw
$openclawDir = "$env:USERPROFILE\.openclaw"
if (Test-Path $openclawDir) {
    Write-Host "  📁 备份 $openclawDir ..." -ForegroundColor Cyan
    Copy-Item -Path $openclawDir -Destination "$backupDir\.openclaw" -Recurse -Force
    Write-Green "  ✅ .openclaw 备份完成"
}

# 备份 workspace
$workspaceDir = "$env:USERPROFILE\.openclaw\workspace"
if (Test-Path $workspaceDir) {
    Write-Host "  📁 备份 workspace ..." -ForegroundColor Cyan
    Copy-Item -Path $workspaceDir -Destination "$backupDir\workspace" -Recurse -Force
    Write-Green "  ✅ workspace 备份完成"
}

# 备份 OpenClaw 源码（如果存在）
$sourceDir = "$env:USERPROFILE\openclaw"
if (Test-Path $sourceDir) {
    Write-Host "  📁 备份 OpenClaw 源码 ..." -ForegroundColor Cyan
    Copy-Item -Path $sourceDir -Destination "$backupDir\openclaw-source" -Recurse -Force
    Write-Green "  ✅ OpenClaw 源码备份完成"
}

# 创建备份信息文件
$backupInfo = @"
OpenClaw 备份信息
==================
备份时间: $(Get-Date)
主机名: $env:COMPUTERNAME
用户名: $env:USERNAME
操作系统: $(Get-CimInstance Win32_OperatingSystem).Caption
OpenClaw 目录: $openclawDir
工作区: $workspaceDir
源码: $sourceDir (如果存在)

备份内容:
- $openclawDir (完整配置)
- $workspaceDir (工作文件)
- $sourceDir (源码, 如果存在)

恢复命令:
Copy-Item -Path "$backupDir\.openclaw" -Destination $env:USERPROFILE\ -Recurse -Force
Copy-Item -Path "$backupDir\workspace" -Destination "$env:USERPROFILE\.openclaw\" -Recurse -Force
"@

Set-Content -Path "$backupDir\backup-info.txt" -Value $backupInfo -Encoding UTF8

Write-Green "  ✅ 备份完成！备份位置: $backupDir"
Write-Host ""

# ============================================
# 第 2 部分：同步 OpenClaw 官方源码
# ============================================
Write-Yellow "📥 第 2 步：同步 OpenClaw 官方源码..."

$openclawSourceDir = "$env:USERPROFILE\.openclaw\openclaw-source"

if (Test-Path $openclawSourceDir) {
    Write-Host "  📁 检测到已有源码目录，更新中..." -ForegroundColor Cyan
    Set-Location $openclawSourceDir
    try {
        git pull origin main 2>$null || git pull origin master 2>$null || Write-Host "  ⚠️  拉取失败，可能是独立开发分支" -ForegroundColor Yellow
        Write-Green "  ✅ 源码已更新"
    } catch {
        Write-Yellow "  ⚠️  更新失败: $_"
    }
} else {
    Write-Host "  📥 克隆 OpenClaw 官方源码..." -ForegroundColor Cyan
    git clone https://github.com/openclaw/openclaw.git $openclawSourceDir
    Write-Green "  ✅ 源码克隆完成"
}
Write-Host ""

# ============================================
# 第 3 部分：检查管理员权限
# ============================================
Write-Yellow "📦 第 3 步：安装系统依赖..."

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Red "⚠️  请以管理员身份运行此脚本！"
    Write-Host "右键点击 PowerShell -> 以管理员身份运行" -ForegroundColor Yellow
    exit 1
}

# 安装 Chocolatey (如果未安装)
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "  📦 正在安装 Chocolatey..." -ForegroundColor Cyan
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# 安装依赖
Write-Host "  📦 安装 Git, Node.js, Python..." -ForegroundColor Cyan
choco install git nodejs python -y

# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 检查 Node.js 版本
try {
    $nodeVersion = (node --version) -replace 'v',''
    $nodeMajor = $nodeVersion.Split('.')[0]
    if ([int]$nodeMajor -lt 18) {
        Write-Host "  ⚠️  Node.js 版本过低，正在更新..." -ForegroundColor Yellow
        choco install nodejs20 -y
    }
} catch {
    Write-Host "  ⚠️  Node.js 未正确安装，尝试安装..." -ForegroundColor Yellow
    choco install nodejs20 -y
}

Write-Green "  ✅ 依赖安装完成"
Write-Host ""

# ============================================
# 第 4 部分：配置 OpenClaw
# ============================================
Write-Yellow "⚙️  第 4 步：配置 OpenClaw..."

# 确保目录存在
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw" -Force | Out-Null

# 如果有源码，复制配置文件
if ((Test-Path $openclawSourceDir) -and (Test-Path "$openclawSourceDir\openclaw-config.json.example")) {
    Copy-Item -Path "$openclawSourceDir\openclaw-config.json.example" -Destination "$env:USERPROFILE\.openclaw\openclaw-config.json" -Force
}

Write-Green "  ✅ 配置完成"
Write-Host ""

# ============================================
# 第 5 部分：启动 OpenClaw
# ============================================
Write-Yellow "🚀 第 5 步：启动 OpenClaw Gateway..."

# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 尝试启动
try {
    & openclaw gateway start 2>$null
} catch {
    Write-Yellow "  ⚠️  openclaw 命令未找到，请先安装 OpenClaw CLI"
    Write-Host "  安装命令: npm install -g openclaw" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Green "✅ 部署完成！"
Write-Host ""
Write-Host "📋 摘要:"
Write-Host "  • 备份位置: $backupDir" -ForegroundColor Cyan
Write-Host "  • 源码位置: $openclawSourceDir" -ForegroundColor Cyan
Write-Host "  • 配置目录: $env:USERPROFILE\.openclaw" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 后续操作:"
Write-Host "  • 查看部署文档: openclaw\deploy\windows-deploy.md" -ForegroundColor Cyan
Write-Host "  • 启动命令: openclaw gateway start" -ForegroundColor Cyan
Write-Host "  • 停止命令: openclaw gateway stop" -ForegroundColor Cyan
Write-Host "  • 状态查看: openclaw gateway status" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔄 更新源码:"
Write-Host "  • 自动更新: %USERPROFILE%\.openclaw\workspace\deploy\sync-source.bat" -ForegroundColor Cyan
Write-Host ""
