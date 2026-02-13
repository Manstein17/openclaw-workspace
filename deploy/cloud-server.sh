#!/bin/bash

# OpenClaw Linux 云服务器部署脚本
# 运行方式: chmod +x cloud-server.sh && ./cloud-server.sh

set -e

echo "☁️  欢迎使用 OpenClaw 云服务器部署脚本！"
echo "========================================"

# 检测包管理器
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    INSTALL_CMD="sudo apt-get update && sudo apt-get install -y"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
elif command -v yum &> /dev/null; then
    PKG_MANAGER="yum"
    INSTALL_CMD="sudo yum install -y"
else
    echo "❌ 不支持的 Linux 发行版"
    exit 1
fi

echo "📦 检测到包管理器: $PKG_MANAGER"

# 安装系统依赖
echo "📦 安装系统依赖..."
$INSTALL_CMD git curl wget build-essential nginx

# 安装 Node.js 20
if ! command -v node &> /dev/null; then
    echo "📦 安装 Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    $INSTALL_CMD nodejs
fi

# 检查 Node.js 版本
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️  Node.js 版本过低，正在更新..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    $INSTALL_CMD nodejs
fi

# 安装 PM2 (进程管理器)
if ! command -v pm2 &> /dev/null; then
    echo "📦 安装 PM2..."
    sudo npm install -g pm2
fi

# 创建工作目录
WORK_DIR="/opt/openclaw"
echo "📁 创建工作目录: $WORK_DIR"
sudo mkdir -p $WORK_DIR
sudo chown $USER:$USER $WORK_DIR

# 克隆仓库
echo "📥 克隆 OpenClaw 仓库..."
cd $WORK_DIR
if [ -d ".git" ]; then
    echo "📁 仓库已存在，更新中..."
    git pull
else
    git clone https://github.com/Manstein17/--botbot.git .
fi

# 安装依赖
echo "📦 安装 Node.js 依赖..."
npm install

# 配置 OpenClaw
echo "⚙️  配置 OpenClaw..."
if [ ! -f "openclaw-config.json" ]; then
    cp openclaw-config.json.example openclaw-config.json 2>/dev/null || true
fi

# 使用 PM2 启动 OpenClaw
echo "🚀 使用 PM2 启动 OpenClaw Gateway..."
pm2 start openclaw-config.json 2>/dev/null || pm2 start --name openclaw "npm start"

# 设置开机自启
echo "⚙️  配置开机自启..."
pm2 startup
pm2 save

# 配置 Nginx 反向代理 (可选)
configure_nginx() {
    echo "⚙️  配置 Nginx 反向代理..."
    sudo tee /etc/nginx/sites-available/openclaw > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF
    sudo ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
}

# 询问是否配置 Nginx
read -p "是否配置 Nginx 反向代理？(y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    configure_nginx
fi

echo ""
echo "✅ 云服务器部署完成！"
echo "📖 查看部署文档: $WORK_DIR/deploy/cloud-server-deploy.md"
echo ""
echo "常用命令:"
echo "  pm2 status          - 查看状态"
echo "  pm2 logs openclaw  - 查看日志"
echo "  pm2 restart openclaw - 重启服务"
