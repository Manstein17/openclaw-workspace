# 🪟 Windows 部署指南

> 本指南将帮助你在 Windows 电脑上安装 OpenClaw。即使你从未接触过编程，也能跟着步骤完成！

---

## 📋 目录

1. [环境要求](#环境要求)
2. [前置条件](#前置条件)
3. [详细安装步骤](#详细安装步骤)
4. [验证安装](#验证安装)
5. [常见问题](#常见问题)

---

## 🖥️ 环境要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| 操作系统 | Windows 10 (1903+) | Windows 11 |
| 内存 | 4GB | 8GB+ |
| 存储空间 | 5GB | 10GB+ |
| 网络 | 需要联网 | 需要联网 |

---

## ✅ 前置条件

在开始之前，你需要准备：

1. ✅ **管理员账户** - 安装软件需要管理员权限
2. ✅ **网络连接** - 需要访问 GitHub
3. ✅ **至少 30 分钟时间** - 首次安装需要一些时间

---

## 📝 详细安装步骤

### 第 1 步：安装 Chocolatey（包管理器）

> 💡 **提示**：Chocolatey 是 Windows 的软件包管理器，帮助你轻松安装各种工具

1. 右键点击 **开始菜单** → 选择 **Windows PowerShell (管理员)**
   
   ![PowerShell](https://via.placeholder.com/400x200?text=Windows+PowerShell)

2. 在打开的窗口中，粘贴以下命令：

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

📌 **注意**：
- 窗口标题会显示 **"管理员: Windows PowerShell"**
- 安装过程中不要关闭窗口

3. 安装完成后，**重启 PowerShell**（关闭后重新以管理员身份打开）

---

### 第 2 步：安装必要软件

在管理员 PowerShell 中依次执行以下命令：

#### 2.1 安装 Git
```powershell
choco install git -y
```

#### 2.2 安装 Node.js
```powershell
choco install nodejs20 -y
```

#### 2.3 安装 Python
```powershell
choco install python -y
```

📌 **验证安装**：完成后重新打开 PowerShell，输入：
```powershell
git --version
node --version
python --version
```

---

### 第 3 步：克隆 OpenClaw 仓库

1. 创建放置代码的文件夹：
```powershell
mkdir -p C:\OpenClaw
cd C:\OpenClaw
```

2. 从 GitHub 克隆代码：
```powershell
git clone https://github.com/Manstein17/--botbot.git .
```

📌 **提示**：如果速度慢，可以尝试：
```powershell
git clone https://ghproxy.com/https://github.com/Manstein17/--botbot.git .
```

---

### 第 4 步：安装项目依赖

```powershell
cd C:\OpenClaw
npm install
```

📌 **提示**：
- 这个过程可能需要 5-10 分钟
- 看到 `added XXX packages` 表示安装成功

---

### 第 5 步：配置 OpenClaw

1. 复制配置文件：
```powershell
copy openclaw-config.json.example openclaw-config.json
```

2. 用记事本打开配置文件：
```powershell
notepad openclaw-config.json
```

3. 根据你的需求修改配置（可选）

---

### 第 6 步：启动 OpenClaw

```powershell
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

```powershell
openclaw gateway status
```

### 方法 2：访问网页

1. 打开浏览器
2. 在地址栏输入：`http://localhost:3000`
3. 如果看到 OpenClaw 界面，说明安装成功！

---

## ❓ 常见问题

### Q1: PowerShell 执行策略错误怎么办？

**错误信息**：
```
无法加载文件，因为在此系统上禁止运行脚本
```

**解决方法**：
1. 以管理员身份打开 PowerShell
2. 执行：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
3. 选择 `A`（全是）

---

### Q2: 安装 Node.js 失败怎么办？

**常见原因**：之前安装过 Node.js 导致冲突

**解决方法**：
1. 卸载现有的 Node.js（通过控制面板 → 程序和功能）
2. 清理残留文件：
   - 删除 `C:\Program Files\nodejs`
   - 删除 `C:\Users\你的用户名\AppData\Roaming\npm`
3. 重新运行安装命令

---

### Q3: npm install 报错怎么办？

**常见错误**：
```
npm WARN deprecated ...
npm ERR! code ELIFECYCLE
```

**解决方法**：
1. 清理缓存：
```powershell
npm cache clean --force
```

2. 删除 node_modules 文件夹：
```powershell
Remove-Item -Recurse -Force node_modules
```

3. 重新安装：
```powershell
npm install
```

---

### Q4: 端口被占用怎么办？

**错误信息**：
```
Error: listen EADDRINUSE: address already in use :::3000
```

**解决方法**：
1. 查找占用端口的进程：
```powershell
netstat -ano | findstr :3000
```

2. 关闭该进程（把 `<PID>` 替换成查到的数字）：
```powershell
taskkill /PID <PID> /F
```

3. 重新启动 OpenClaw：
```powershell
openclaw gateway start
```

---

### Q5: 中文显示乱码怎么办？

**解决方法**：
1. 在 PowerShell 中执行：
```powershell
chcp 65001
```

2. 或者右键 PowerShell 标题栏 → 属性 → 选择 **Lucida Console**

---

### Q6: 如何开机自启 OpenClaw？

**方法 1：使用任务计划程序**
1. 搜索 "任务计划程序"
2. 创建基本任务
3. 设置触发器为 "计算机启动"
4. 操作选择 "启动程序"
5. 程序填写：`C:\OpenClaw\start.bat`

**方法 2：使用 PM2**
```powershell
npm install -g pm2
pm2 start "npm start" --name openclaw
pm2 startup
pm2 save
```

---

### Q7: 如何更新 OpenClaw？

```powershell
cd C:\OpenClaw
git pull
npm install
openclaw gateway restart
```

---

### Q8: 如何卸载 OpenClaw？

```powershell
cd C:\
Remove-Item -Recurse -Force OpenClaw
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

你已成功在 Windows 上部署 OpenClaw！现在可以开始使用了。

**下一步**：
- 📖 阅读 SOUL.md 了解 OpenClaw 的工作方式
- ⚙️ 配置你需要的插件和功能
- 🎮 开始使用 OpenClaw！
