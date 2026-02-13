# 🤖 OpenClaw 跨平台部署指南

> 通过 GitHub 在任何设备上部署 OpenClaw

**GitHub 仓库**: https://github.com/Manstein17/--botbot.git

---

## 📋 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Manstein17/--botbot.git
cd --botbot

# 2. 运行部署脚本
./deploy/mac.sh      # macOS
./deploy/linux.sh    # Linux
./deploy/cloud-server.sh  # 云服务器
./deploy/android.sh  # Android (Termux)
```

---

## 🖥️ 各平台部署指南

| 平台 | 快速命令 | 详细文档 |
|------|---------|---------|
| 🍎 macOS | `./deploy/mac.sh` | [mac-deploy.md](deploy/mac-deploy.md) |
| 🪟 Windows | `.\deploy\windows.ps1` | [windows-deploy.md](deploy/windows-deploy.md) |
| 🐧 Linux | `./deploy/linux.sh` | [linux-deploy.md](deploy/linux-deploy.md) |
| ☁️ 云服务器 | `./deploy/cloud-server.sh` | [cloud-server-deploy.md](deploy/cloud-server-deploy.md) |
| 📱 Android | `./deploy/android.sh` | [android-deploy.md](deploy/android-deploy.md) |

---

## 📦 备份内容

本仓库包含：
- OpenClaw 配置文件 (AGENTS.md, SOUL.md, TOOLS.md, USER.md, HEARTBEAT.md)
- 每日记忆 (memory/)
- 技能和脚本 (skills/, scripts/)
- 项目代码 (projects/)
- 部署脚本 (deploy/)

---

## 🔄 每日备份

OpenClaw 每天 21:00 自动备份到本仓库。

手动备份：
```bash
~/.openclaw/openclaw-backup.sh
```

---

## ❓ 常见问题

### Q: 部署失败怎么办？
A: 查看对应平台的详细部署文档中的"常见问题"部分

### Q: 如何更新到最新版本？
A: 
```bash
git pull origin main
npm install
openclaw gateway restart
```

### Q: 需要帮助怎么办？
A: 查看各平台的详细部署文档，或提交 GitHub Issue

---

## 📝 文档更新日志

- 2026-02-13: 添加 macOS, Windows, Linux, 云服务器, Android 部署指南
