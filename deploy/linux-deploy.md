# 🐧 Linux 桌面部署指南

> 本指南将帮助你在 Linux 桌面上安装 OpenClaw。即使你从未接触过编程，也能跟着步骤完成！

---

## 📋 目录

1. [环境要求](#环境要求)
2. [支持的发行版](#支持的发行版)
3. [详细安装步骤](#详细安装步骤)
4. [验证安装](#验证安装)
5. [常见问题](#常见问题)

---

## 🖥️ 环境要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Ubuntu 20.04 / Debian 11 / Fedora 35+ | Ubuntu 22.04 / Debian 12 |
| 内存 | 4GB | 8GB+ |
| 存储空间 | 5GB | 10GB+ |
| 网络 | 需要联网 | 需要联网 |

---

## 📌 支持的发行版

本脚本支持以下 Linux 发行版：

- ✅ **Ubuntu** (20.04, 22.04, 24.04)
- ✅ **Debian** (11, 12)
- ✅ **Fedora** (35, 36, 37, 38, 39)
- ✅ **CentOS** / **RHEL** (8, 9)
- ✅ **Arch Linux** / **Manjaro**
- ✅ **openSUSE**

---

## 📝 详细安装步骤

### 第 1 步：打开终端

> 💡 **提示**：终端是 Linux 的命令行工具

在系统中搜索 **Terminal** 或 **终端**，点击打开。

![终端图标](https://via.placeholder.com/150x100?text=Terminal)

---

### 第 2 步：更新系统包列表

```bash
sudo apt update   # Ubuntu/Debian
# 或者
sudo dnf check-update   # Fedora
# 或者
sudo pacman -Sy   # Arch/Manjaro
```

📌 **注意**：
- `sudo` 表示以管理员权限运行
- 需要输入你的用户密码

---

### 第 3 步：安装必要软件

根据你的发行版选择命令：

#### Ubuntu / Debian:
```bash
sudo apt install -y git curl wget build-essential
```

#### Fedora:
```bash
sudo dnf install -y git curl wget make gcc gcc-c++
```

#### Arch / Manjaro:
```bash
sudo pacman -S --noconfirm git curl wget base-devel
```

---

### 第 4 步：安装 Node.js

#### Ubuntu / Debian:
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

#### Fedora:
```bash
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs
```

#### Arch / Manjaro:
```bash
sudo pacman -S --noconfirm nodejs npm
```

📌 **验证安装**：
```bash
node --version
npm --version
```

---

### 第 5 步：安装 OpenClaw CLI

```bash
sudo npm install -g openclaw
```

📌 **验证安装**：
```bash
openclaw --version
```

---

### 第 6 步：克隆 OpenClaw 仓库

```bash
mkdir -p ~/OpenClaw
cd ~/OpenClaw
git clone https://github.com/Manstein17/--botbot.git .
```

📌 **提示**：如果速度慢，可以尝试：
```bash
git clone https://ghproxy.com/https://github.com/Manstein17/--botbot.git .
```

---

### 第 7 步：安装项目依赖

```bash
cd ~/OpenClaw
npm install
```

📌 **提示**：
- 这个过程可能需要几分钟
- 看到 `added XXX packages` 表示安装成功

---

### 第 8 步：配置 OpenClaw

1. 复制配置文件：
```bash
cp openclaw-config.json.example openclaw-config.json
```

2. 用文本编辑器打开：
```bash
nano openclaw-config.json
```

3. 修改完成后：
   - 按 `Ctrl + O` 保存
   - 按 `Ctrl + X` 退出

---

### 第 9 步：启动 OpenClaw

```bash
openclaw gateway start
```

如果看到类似以下信息，说明启动成功：

```
🚀 OpenClaw Gateway 正在启动...
✅ Gateway 已启动，监听端口: 3000
```

---

## ✅ 验证安装

### 方法 1：检查服务状态

```bash
openclaw gateway status
```

### 方法 2：访问网页

1. 打开浏览器（Firefox 或 Chrome）
2. 在地址栏输入：`http://localhost:3000`
3. 如果看到 OpenClaw 界面，说明安装成功！

---

## 🔧 常用命令

| 命令 | 说明 |
|------|------|
| `openclaw gateway start` | 启动服务 |
| `openclaw gateway stop` | 停止服务 |
| `openclaw gateway status` | 查看状态 |
| `openclaw gateway restart` | 重启服务 |

---

## ❓ 常见问题

### Q1: 提示 "command not found" 怎么办？

**解决方法**：
1. 刷新环境变量：
```bash
source ~/.bashrc
```

2. 或者手动添加到 PATH：
```bash
export PATH=$PATH:/usr/local/bin
```

---

### Q2: npm install 报错怎么办？

**常见错误**：
```
npm WARN deprecated ...
npm ERR! code ELIFECYCLE
```

**解决方法**：
1. 清理缓存：
```bash
npm cache clean --force
```

2. 删除 node_modules：
```bash
rm -rf node_modules
```

3. 重新安装：
```bash
npm install
```

---

### Q3: 端口被占用怎么办？

**错误信息**：
```
Error: listen EADDRINUSE: address already in use :::3000
```

**解决方法**：
1. 查找占用端口的进程：
```bash
sudo lsof -i :3000
```

2. 关闭该进程：
```bash
sudo kill -9 <PID>
```

3. 重新启动 OpenClaw：
```bash
openclaw gateway start
```

---

### Q4: 如何使用桌面快捷方式？

1. 创建启动器文件：
```bash
nano ~/.local/share/applications/openclaw.desktop
```

2. 添加以下内容：
```ini
[Desktop Entry]
Type=Application
Name=OpenClaw
Exec=openclaw gateway start
Icon=terminal
Terminal=true
```

3. 保存后，在应用菜单中搜索 "OpenClaw" 即可找到

---

### Q5: 如何开机自启？

**方法 1：使用 systemd**
```bash
sudo nano /etc/systemd/system/openclaw.service
```

添加以下内容：
```ini
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
User=你的用户名
WorkingDirectory=/home/你的用户名/OpenClaw
ExecStart=/usr/bin/openclaw gateway start
Restart=always

[Install]
WantedBy=multi-user.target
```

启用服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable openclaw
sudo systemctl start openclaw
```

**方法 2：使用 .desktop 自启动**
```bash
cp ~/.local/share/applications/openclaw.desktop ~/.config/autostart/
```

---

### Q6: 如何更新 OpenClaw？

```bash
cd ~/OpenClaw
git pull
npm install
openclaw gateway restart
```

---

### Q7: 如何卸载 OpenClaw？

```bash
cd ~
rm -rf OpenClaw
npm uninstall -g openclaw
```

---

## 📞 获取帮助

如果遇到无法解决的问题：

1. 📖 查看 [OpenClaw 官方文档](https://github.com/Manstein17/--botbot)
2. 💬 在 GitHub 提交 [Issue](https://github.com/Manstein17/--botbot/issues)
3. 🔧 检查网络连接是否正常

---

## 🎉 恭喜！

你已成功在 Linux 上部署 OpenClaw！现在可以开始使用了。

**下一步**：
- 📖 阅读 SOUL.md 了解 OpenClaw 的工作方式
- ⚙️ 配置你需要的插件和功能
- 🎮 开始使用 OpenClaw！
