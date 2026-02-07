# 空投情报局 Pro - 快速使用指南

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的 API Keys
```

### 3. 初始化数据库
```bash
npx prisma migrate dev
npx prisma db seed
```

### 4. 启动开发服务器
```bash
npm run dev
```

访问 http://localhost:3000

---

## 📡 脚本使用说明

### Discord 空投监控

监控 Discord 频道中的空投信息：
```bash
# 完整监控（需要 Discord Bot Token）
node scripts/discord-airdrop-monitor.js

# 模拟模式（无 Token 时使用）
node scripts/discord-airdrop-monitor.js --simulate
```

### 全网空投搜索

使用 Brave API 搜索全网空投资讯：
```bash
# 执行搜索
node scripts/search-airdrops.js

# 搜索特定项目
node scripts/search-airdrops.js --project "LayerZero"
```

### 一键执行所有监控

```bash
# 执行完整监控流程
bash scripts/run-airdrop-monitor.sh

# 仅执行搜索
bash scripts/run-airdrop-monitor.sh search

# 仅执行 Discord 监控
bash scripts/run-airdrop-monitor.sh discord

# 查看统计信息
bash scripts/run-airdrop-monitor.sh stats

# 实时查看日志
bash scripts/run-airdrop-monitor.sh log
```

---

## ⏰ Cron 自动任务配置

### 查看当前 Cron 任务
```bash
openclaw cron list
```

### 查看任务状态
```bash
openclaw cron status
```

### 手动运行任务
```bash
openclaw cron run <task-id>
```

### 查看任务运行历史
```bash
openclaw cron runs
```

---

## 📁 文件结构

```
airdrop-intelligence-pro/
├── scripts/
│   ├── discord-airdrop-monitor.js  # Discord 监控脚本
│   ├── search-airdrops.js          # 全网搜索脚本
│   └── run-airdrop-monitor.sh     # 一键执行脚本
├── app/
│   ├── dashboard/                  # Dashboard 页面
│   ├── airdrops/
│   │   ├── add/page.tsx            # 添加监控项目
│   │   └── [id]/page.tsx          # 空投详情页
│   ├── reports/page.tsx            # 报告生成页
│   └── alerts/page.tsx             # 提醒设置页
├── lib/
│   └── prisma/                     # 数据库配置
└── logs/
    └── airdrop-monitor.log         # 监控日志
```

---

## 🔧 API 配置

### Discord Bot 设置
1. 访问 [Discord Developer Portal](https://discord.com/developers/applications)
2. 创建新应用 → "New Application"
3. 在 "Bot" 页面 → "Add Bot"
4. 复制 Bot Token 到 `.env`
5. 在 "OAuth2" 页面生成邀请链接

### Brave Search API
1. 访问 [Brave API](https://api.search.brave.com/)
2. 注册账号并获取 API Key
3. 将 Key 填入 `.env`

### Telegram 通知
1. 与 @BotFather 对话创建机器人
2. 获取 Bot Token
3. 与 @userinfobot 获取 Chat ID
4. 填入 `.env`

---

## 📊 功能特性

- ✅ **Discord 监控** - 自动检测热门项目的空投动态
- ✅ **全网搜索** - 每日自动搜索新的空投资讯
- ✅ **智能提醒** - 支持邮件/Telegram 通知
- ✅ **任务追踪** - 管理空投任务完成进度
- ✅ **报告生成** - 导出 PDF/Excel/CSV 报告
- ✅ **自动执行** - 每30分钟自动搜索更新

---

## 🐛 常见问题

### Q: Discord 监控不工作？
A: 确保已配置 `DISCORD_BOT_TOKEN`，且 Bot 已被添加到目标服务器

### Q: Brave 搜索失败？
A: 检查 `BRAVE_API_KEY` 是否有效，或在 `.env` 中留空使用模拟模式

### Q: 如何查看日志？
```bash
tail -f ~/.openclaw/logs/airdrop-monitor.log
```

### Q: 如何添加新的监控项目？
访问 Dashboard → 点击"添加监控项目" → 搜索并添加

---

## 📝 日志位置

- 主日志: `~/.openclaw/logs/airdrop-monitor.log`
- Discord 监控日志: `~/.openclaw/logs/discord-monitor.log`
- 搜索日志: `~/.openclaw/logs/airdrop-search.log`
