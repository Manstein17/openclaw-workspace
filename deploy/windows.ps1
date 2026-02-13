# OpenClaw Windows 部署脚本
# 运行方式: 右键以管理员身份运行 PowerShell，然后执行 .\windows.ps1

Write-Host "🪟 欢迎使用 OpenClaw Windows 部署脚本！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 检查管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  请以管理员身份运行此脚本！" -ForegroundColor Yellow
    Write-Host "右键点击 PowerShell -> 以管理员身份运行" -ForegroundColor Yellow
    exit 1
}

# 安装 Chocolatey (如果未安装)
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "📦 正在安装 Chocolatey..." -ForegroundColor Cyan
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
}

# 安装依赖
Write-Host "📦 安装依赖..." -ForegroundColor Cyan
choco install git nodejs python -y

# 刷新环境变量
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 检查 Node.js 版本
$nodeVersion = (node --version) -replace 'v',''
$nodeMajor = $nodeVersion.Split('.')[0]
if ([int]$nodeMajor -lt 18) {
    Write-Host "⚠️  Node.js 版本过低，正在更新..." -ForegroundColor Yellow
    choco install nodejs20 -y
}

# 克隆仓库
Write-Host "📥 克隆 OpenClaw 仓库..." -ForegroundColor Cyan
if (Test-Path "openclaw") {
    Write-Host "📁 openclaw 目录已存在，跳过克隆" -ForegroundColor Yellow
    Set-Location openclaw
} else {
    git clone https://github.com/Manstein17/--botbot.git openclaw
    Set-Location openclaw
}

# 安装依赖
Write-Host "📦 安装 Node.js 依赖..." -ForegroundColor Cyan
npm install

# 配置 OpenClaw
Write-Host "⚙️  配置 OpenClaw..." -ForegroundColor Cyan
if (-not (Test-Path "openclaw-config.json")) {
    if (Test-Path "openclaw-config.json.example") {
        Copy-Item "openclaw-config.json.example" "openclaw-config.json"
    }
}

# 启动 OpenClaw Gateway
Write-Host "🚀 启动 OpenClaw Gateway..." -ForegroundColor Cyan
Start-Process -FilePath "openclaw" -ArgumentList "gateway", "start" -NoNewWindow

Write-Host ""
Write-Host "✅ 部署完成！" -ForegroundColor Green
Write-Host "📖 查看部署文档: openclaw\deploy\windows-deploy.md" -ForegroundColor Green
