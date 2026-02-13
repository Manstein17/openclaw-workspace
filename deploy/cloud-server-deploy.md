# ☁️ 云服务器部署指南

> 本指南将帮助你在 Linux 云服务器上部署 OpenClaw。适用于阿里云、腾讯云、AWS、DigitalOcean 等云服务商！

---

## 📋 目录

1. [环境要求](#环境要求)
2. [服务器配置建议](#服务器配置建议)
3. [详细安装步骤](#详细安装步骤)
4. [配置 Nginx 反向代理](#配置-nginx-反向代理)
5. [配置 HTTPS (SSL)](#配置-https-ssl)
6. [验证安装](#验证安装)
7. [常用管理命令](#常用管理命令)
8. [常见问题](#常见问题)

---

## 🖥️ 环境要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 20.04 / CentOS 8 | Ubuntu 22.04 / Debian 12 |
| CPU | 1 核 | 2 核+ |
| 内存 | 2GB | 4GB+ |
| 带宽 | 1Mbps | 5Mbps+ |
| 存储 | 10GB | 20GB+ |

---

## 🏭 服务器配置建议

### 入门级（个人使用）
- **CPU**: 1 核
- **内存**: 2GB
- **带宽**: 1-3 Mbps
- **系统盘**: 20GB SSD
- **价格**: ~¥30/月

### 生产级（团队使用）
- **CPU**: 2 核
- **内存**: 4GB
- **带宽**: 5-10 Mbps
- **系统盘**: 40GB SSD
- **价格**: ~¥80/月

---

## 📝 详细安装步骤

### 第 1 步：连接服务器

> 💡 **提示**：使用 SSH 客户端连接服务器

#### Windows 用户：
1. 下载并安装 [PuTTY](https://putty.org/) 或 [Windows Terminal](https://aka.ms/terminal)
2. 输入服务器 IP 地址
3. 输入用户名和密码

#### Mac / Linux 用户：
打开终端，输入：
```bash
ssh root@你的服务器IP
```

📌 **首次连接**：会提示确认密钥，输入 `yes` 后继续

---

### 第 2 步：更新系统

```bash
# Ubuntu/Debian
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

---

### 第 3 步：创建普通用户（安全建议）

> 💡 **提示**：不要使用 root 用户运行应用，这是安全最佳实践

```bash
# 创建用户（把 openclaw 改成你喜欢的名字）
adduser openclaw

# 给用户 sudo 权限
usermod -aG sudo openclaw

# 切换到该用户
su - openclaw
```

---

### 第 4 步：安装 Node.js 20

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo yum install -y nodejs
```

📌 **验证安装**：
```bash
node --version
npm --version
```

---

### 第 5 步：安装 PM2（进程管理器）

```bash
sudo npm install -g pm2
```

📌 **为什么用 PM2**？
- 自动重启崩溃的应用
- 开机自启
- 负载均衡
- 查看日志

---

### 第 6 步：克隆 OpenClaw 仓库

```bash
# 创建工作目录
sudo mkdir -p /opt/openclaw
sudo chown $USER:$USER /opt/openclaw

# 进入目录
cd /opt/openclaw

# 克隆代码
git clone https://github.com/Manstein17/--botbot.git .
```

📌 **提示**：如果速度慢：
```bash
git clone https://ghproxy.com/https://github.com/Manstein17/--botbot.git .
```

---

### 第 7 步：安装项目依赖

```bash
npm install
```

---

### 第 8 步：配置 OpenClaw

```bash
cp openclaw-config.json.example openclaw-config.json
nano openclaw-config.json
```

根据需要修改配置，保存退出。

---

### 第 9 步：使用 PM2 启动

```bash
# 启动应用
pm2 start --name openclaw "npm start"

# 保存当前进程列表（用于开机自启）
pm2 save

# 设置开机自启
pm2 startup
```

📌 **提示**：最后一行命令会输出类似这样的内容：
```
[PM2] You have to run this command as root. Execute the following command:
sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup ...
```

请**复制并执行**输出的命令！

---

## 🔄 配置 Nginx 反向代理

> 💡 **提示**：反向代理让你可以通过域名直接访问，不需要输入端口号

### 第 1 步：安装 Nginx

```bash
# Ubuntu/Debian
sudo apt install -y nginx

# CentOS/RHEL
sudo yum install -y nginx
```

### 第 2 步：创建配置文件

```bash
sudo nano /etc/nginx/sites-available/openclaw
```

添加以下内容：

```nginx
server {
    listen 80;
    server_name 你的域名或服务器IP;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 第 3 步：启用配置

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 🔒 配置 HTTPS (SSL)

> 💡 **提示**：使用 Let's Encrypt 免费获取 SSL 证书

### 使用 Certbot（推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书（按照提示操作）
sudo certbot --nginx -d your-domain.com

# 如果只有 IP
sudo certbot --nginx --standalone -d your-domain.com
```

📌 **自动续期**：Let's Encrypt 证书 90 天过期，Certbot 会自动续期！

---

## ✅ 验证安装

### 方法 1：PM2 状态
```bash
pm2 status
```

### 方法 2：访问网站
在浏览器中输入你的服务器 IP 或域名，应该能看到 OpenClaw 界面！

### 方法 3：检查日志
```bash
pm2 logs openclaw
```

---

## 📟 常用管理命令

| 命令 | 说明 |
|------|------|
| `pm2 status` | 查看运行状态 |
| `pm2 logs openclaw` | 查看日志 |
| `pm2 restart openclaw` | 重启服务 |
| `pm2 stop openclaw` | 停止服务 |
| `pm2 delete openclaw` | 删除服务 |
| `pm2 monit` | 实时监控面板 |

---

## 🔧 防火墙配置

### Ubuntu (UFW)
```bash
# 开放端口
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP
sudo ufw allow 443     # HTTPS
sudo ufw allow 3000    # OpenClaw 端口（仅限开发环境）

# 启用防火墙
sudo ufw enable
```

### CentOS (firewalld)
```bash
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

---

## ❓ 常见问题

### Q1: 无法连接服务器？

**检查**：
1. 服务器 IP 是否正确
2. 防火墙是否开放 22 端口
3. 云服务器安全组是否开放端口

---

### Q2: PM2 启动失败？

**常见错误**：
```
Error: spawn npm ENOENT
```

**解决方法**：
1. 使用绝对路径：
```bash
pm2 start --name openclaw /usr/bin/npm -- start
```

---

### Q3: 端口被占用？

**解决方法**：
```bash
# 查找占用端口的进程
sudo lsof -i :3000

# 关闭进程
sudo kill -9 <PID>
```

---

### Q4: Nginx 启动失败？

**检查配置**：
```bash
sudo nginx -t
```

**查看错误日志**：
```bash
sudo tail -f /var/log/nginx/error.log
```

---

### Q5: 如何更新 OpenClaw？

```bash
cd /opt/openclaw
git pull
npm install
pm2 restart openclaw
```

---

### Q6: 如何备份数据？

```bash
# 备份整个项目目录
cd /opt
sudo tar -czvf openclaw-backup-$(date +%Y%m%d).tar.gz openclaw

# 备份到本地电脑
scp root@服务器IP:/opt/openclaw-backup-*.tar.gz ./
```

---

### Q7: 服务器重启后怎么办？

PM2 已经配置了开机自启，如果没自动启动：
```bash
pm2 resurrect
```

---

### Q8: 如何完全卸载？

```bash
# 停止并删除 PM2 进程
pm2 delete openclaw
pm2 save

# 删除文件
cd /opt
sudo rm -rf openclaw

# 删除 Nginx 配置
sudo rm /etc/nginx/sites-available/openclaw
sudo rm /etc/nginx/sites-enabled/openclaw
sudo systemctl restart nginx
```

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. 📖 查看 [OpenClaw 官方文档](https://github.com/Manstein17/--botbot)
2. 💬 在 GitHub 提交 [Issue](https://github.com/Manstein17/--botbot/issues)
3. 📧 联系云服务商技术支持

---

## 🎉 恭喜！

你已成功在云服务器上部署 OpenClaw！现在可以通过域名从任何地方访问了。

**下一步**：
- 📖 阅读 SOUL.md 了解 OpenClaw 的工作方式
- ⚙️ 配置你需要的插件和功能
- 🌐 配置域名解析
- 🔒 启用 HTTPS
