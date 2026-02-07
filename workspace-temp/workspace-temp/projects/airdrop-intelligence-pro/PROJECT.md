# 空投情报局 Pro - 产品设计文档

**产品名称：** 空投情报局 Pro (Airdrop Intelligence Pro)
**版本：** v1.0
**创建时间：** 2026-02-07
**状态：** 产品设计

---

## 一、产品概述

### 1.1 产品定位

**使命：** 提供专业的空投资讯监控与提醒服务

**目标用户：**
- 加密货币投资者
- 撸毛/空投爱好者
- 时间有限的上班族
- 愿意为信息付费的用户

### 1.2 产品形态

| 平台 | 优先级 | 说明 |
|------|--------|------|
| **Web端 (SaaS)** | P0 | 先做，迭代快 |
| **桌面端 (Electron)** | P1 | 后做，24小时监控 |

### 1.3 商业模式

**定价策略：** 低定价试水，根据市场调整

| 套餐 | 价格 | 时长 | 权益 |
|------|------|------|------|
| **体验卡** | ¥9.9 | 7天 | 基础功能 |
| **月卡** | ¥29 | 30天 | 全部功能 |
| **季卡** | ¥79 | 90天 | 全部功能 + 优先 |
| **年卡** | ¥199 | 365天 | 全部功能 + 优先 + 社群 |
| **终身卡** | ¥499 | 永久 | 全部功能 + 优先 + 社群 + 未来产品 |

---

## 二、功能设计

### 2.1 核心功能

#### 功能1：空投监控

| 子功能 | 说明 | 实现方式 |
|--------|------|---------|
| 实时监控 | 7x24小时监控新空投 | 爬虫 + API |
| 多源聚合 | 聚合Twitter/Discord/官网 | 数据采集 |
| 去重筛选 | AI自动去重 + 质量筛选 | 算法 |
| 价值评估 | 自动评估空投潜力 | 评分模型 |

#### 功能2：实时推送

| 子功能 | 说明 | 实现方式 |
|--------|------|---------|
| 站内通知 | Web端实时弹窗 | WebSocket |
| 浏览器推送 | Chrome/Safari通知 | Service Worker |
| 邮件推送 | 重要机会邮件提醒 | SMTP |
| Telegram联动 | 同步推送到Telegram | Telegram Bot API |

#### 功能3：操作指南

| 子功能 | 说明 | 实现方式 |
|--------|------|---------|
| 步骤教程 | 手把手图文教程 | Markdown + 截图 |
| 视频教程 | 进阶项目视频演示 | 视频托管 |
| 进度追踪 | 记录用户完成进度 | 数据库 |
| 交互式引导 | 分步引导完成操作 | 前端组件 |

#### 功能4：社群集成

| 子功能 | 说明 | 实现方式 |
|--------|------|---------|
| 用户社区 | 付费用户专属群 | Telegram/Discord |
| 经验分享 | 用户互相分享 | 论坛形式 |
| 官方答疑 | 团队答疑 | 工单系统 |
| 数据同步 | 跨设备同步 | 账号体系 |

---

### 2.2 用户系统

#### 注册登录

| 方式 | 说明 |
|------|------|
| 邮箱注册 | 基础方式 |
| 第三方登录 | Google/GitHub/Apple |
| 钱包登录 | MetaMask连接（Web3风格）|

#### 账号体系

| 功能 | 说明 |
|------|------|
| 用户分级 | 免费/体验/付费/终身 |
| 设备限制 | 限制同时登录设备数 |
| 续费管理 | 套餐管理、到期提醒 |

#### 激活码系统

| 功能 | 说明 |
|------|------|
| 激活码生成 | 后台生成、批量生成 |
| 激活码验证 | 唯一性校验、防重放 |
| 有效期管理 | 自动计算到期时间 |
| 激活记录 | 记录激活IP/时间/设备 |

---

### 2.3 数据系统

#### 监控数据

| 数据源 | 监控频率 | 内容 |
|--------|---------|------|
| Twitter/X | 每5分钟 | 官方账号、KOL |
| Discord | 每10分钟 | 官方服务器 |
| 项目官网 | 每1小时 | 公告、博客 |
| 开发者社区 | 每2小时 | GitHub、Medium |
| 加密媒体 | 每1小时 | 新闻、评测 |

#### 用户数据

| 数据类型 | 存储 | 说明 |
|----------|------|------|
| 账号信息 | 数据库 | 加密存储 |
| 监控偏好 | 数据库 | JSON格式 |
| 操作记录 | 数据库 | 行为追踪 |
| 订阅状态 | 数据库 | 有效期管理 |

---

## 三、技术架构

### 3.1 Web端技术栈

#### 前端技术

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| **框架** | Next.js 14 | SSR + SEO友好 |
| **UI组件** | Tailwind CSS + Shadcn/UI | 快速开发 |
| **状态管理** | Zustand | 轻量级 |
| **数据获取** | TanStack Query | 缓存管理 |
| **图表** | Recharts | 简洁美观 |
| **推送** | Service Worker | 浏览器推送 |
| **部署** | Vercel | 免费 + 全球CDN |

#### 后端技术

| 层级 | 技术选型 | 理由 |
|------|---------|------|
| **框架** | Next.js API Routes | 前后端统一 |
| **数据库** | PostgreSQL + Prisma | 关系型 + 类型安全 |
| **缓存** | Redis | 高速缓存 |
| **认证** | NextAuth.js | 完善生态 |
| **任务调度** | BullMQ | 可靠队列 |
| **爬虫** | Puppeteer + Cheerio | 灵活采集 |
| **监控** |cron jobs | 定时任务 |

### 3.2 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户层                                │
├─────────────────────────────────────────────────────────────┤
│                     Web浏览器                               │
│         (Chrome/Safari/Firefox/Edge)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      CDN层                                  │
├─────────────────────────────────────────────────────────────┤
│                         Vercel                              │
│                    (全球CDN加速)                           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 应用层                           │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   前端页面    │  │   API接口    │  │  WebSocket  │    │
│  │  (React)    │  │  (REST)     │  │  (实时推送)  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   数据层      │   │   任务层      │   │   第三方层    │
├──────────────┤   ├──────────────┤   ├──────────────┤
│ PostgreSQL   │   │ BullMQ队列   │   │ Brave API    │
│ (用户数据)    │   │ (定时爬虫)   │   │ (搜索增强)   │
│              │   │              │   │              │
│ Redis        │   │ Cron Jobs    │   │ Twitter API  │
│ (缓存/会话)   │   │ (定时任务)   │   │ (数据采集)   │
│              │   │              │   │              │
│              │   │ Puppeteer    │   │ Telegram API │
│              │   │ (页面爬虫)    │   │ (推送通知)   │
└──────────────┘   └──────────────┘   └──────────────┘
```

### 3.3 核心模块设计

#### 模块1：用户系统

```
用户系统
├── 认证模块
│   ├── 邮箱密码登录
│   ├── 第三方OAuth (Google/GitHub/Apple)
│   └── 钱包MetaMask登录
│
├── 订阅管理
│   ├── 套餐选择
│   ├── 激活码验证
│   ├── 有效期计算
│   └── 续费提醒
│
└── 偏好设置
    ├── 监控偏好 (关注哪些类型)
    ├── 推送方式 (邮件/WebPush/Telegram)
    └── 提醒级别 (全部/仅重要)
```

#### 模块2：空投监控系统

```
空投监控系统
├── 数据采集
│   ├── Twitter采集器
│   │   ├── 官方账号监控 (@账号列表)
│   │   ├── KOL账号监控
│   │   └── 关键词搜索
│   │
│   ├── Discord采集器
│   │   ├── 官方服务器监控
│   │   ├── 新频道发现
│   │   └── 公告频道抓取
│   │
│   ├── Web采集器
│   │   ├── 项目官网监控
│   │   ├── 博客/RSS监控
│   │   └── 开发者社区监控
│   │
│   └── 媒体采集器
│       ├── 加密新闻媒体
│       ├── 项目评测网站
│       └── 空投聚合网站
│
├── 数据处理
│   ├── 去重算法
│   │   ├── URL去重
│   │   ├── 标题相似度去重
│   │   └── 内容指纹去重
│   │
│   ├── 质量评估
│   │   ├── 项目可信度评分
│   │   ├── 空投确定性评分
│   │   ├── 参与门槛评分
│   │   └── 综合评分算法
│   │
│   └── 分类打标
│       ├── 类型分类 (Testnet/主网/协议)
│       ├── 阶段分类 (预热/进行中/已结束)
│       └── 风险分级 (低/中/高)
│
└── 存储管理
    ├── MySQL/PostgreSQL存储
    ├── Redis缓存
    └── Elasticsearch搜索
```

#### 模块3：推送系统

```
推送系统
├── 推送通道
│   ├── WebSocket推送
│   │   ├── 连接管理
│   │   └── 消息路由
│   │
│   ├── 浏览器推送
│   │   ├── Service Worker注册
│   │   └── 推送通知发送
│   │
│   ├── 邮件推送
│   │   ├── 模板引擎
│   │   └── SMTP发送
│   │
│   └── Telegram推送
│       ├── Bot API集成
│       └── 消息模板
│
├── 推送策略
│   ├── 推送时机
│   │   ├── 实时推送 (发现即推送)
│   │   ├── 定时推送 (每日汇总)
│   │   └── 批量推送 (每小时汇总)
│   │
│   └── 推送频率控制
│       ├── 单用户频率限制
│       └── 免打扰时段
│
└── 推送追踪
    ├── 打开率统计
    ├── 点击率追踪
    └── 转化率分析
```

#### 模块4：操作指南系统

```
操作指南系统
├── 指南内容管理
│   ├── Markdown编辑器
│   ├── 图片上传
│   ├── 视频托管
│   └── 版本管理
│
├── 指南模板
│   ├── 标准模板 (适用大多数项目)
│   ├── 进阶模板 (复杂操作)
│   └── 视频模板 (视频演示)
│
├── 交互式引导
│   ├── 分步引导组件
│   ├── 进度追踪
│   └── 完成确认
│
└── 用户贡献
    ├── 用户投稿
    ├── 社区编辑
    └── 评分评论
```

---

### 3.4 数据库设计

#### 核心表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    wallet_address VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 订阅表
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    plan_type VARCHAR(50) NOT NULL, --体验/月卡/季卡/年卡/终身
    activation_code VARCHAR(100),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 激活码表
CREATE TABLE activation_codes (
    id UUID PRIMARY KEY,
    code VARCHAR(100) UNIQUE NOT NULL,
    plan_type VARCHAR(50) NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_by UUID REFERENCES users(id),
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 空投项目表
CREATE TABLE airdrop_projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100), --testnet/defi/nft/layer2
    status VARCHAR(50) DEFAULT 'discovered', --discovered/verified/expired
    source_url TEXT,
    source_type VARCHAR(50), --twitter/discord/website/media
    score DECIMAL(3,2), --0-100综合评分
    risk_level VARCHAR(20), --low/medium/high
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 空投资讯表
CREATE TABLE airdrop_updates (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES airdrop_projects(id),
    title VARCHAR(500) NOT NULL,
    content TEXT,
    update_type VARCHAR(50), --announcement/activity/tips/guide
    importance VARCHAR(20), --low/medium/high/critical
    is_pushed BOOLEAN DEFAULT FALSE,
    pushed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 用户偏好表
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    notification_channels JSONB, --['websocket', 'webpush', 'email', 'telegram']
    notification_types JSONB, --['critical', 'high', 'medium']
    quiet_hours JSONB, --{start: '22:00', end: '08:00'}
    tracked_categories JSONB, --['testnet', 'defi', 'nft', 'layer2']
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 操作指南表
CREATE TABLE guides (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES airdrop_projects(id),
    title VARCHAR(500) NOT NULL,
    content TEXT, --Markdown格式
    difficulty VARCHAR(20), --beginner/intermediate/advanced
    estimated_time VARCHAR(50), --'30分钟'
    steps JSONB, --分步骤内容
    images JSONB, --截图数组
    video_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户操作记录表
CREATE TABLE user_actions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    guide_id UUID REFERENCES guides(id),
    status VARCHAR(50), --in_progress/completed
    current_step INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 四、开发计划

### 4.1 MVP版本 (Web端)

**目标：** 最简可用产品，验证市场

**开发周期：** 4-6周

#### 第1周：基础架构

| 任务 | 负责人 | 产出 |
|------|-------|------|
| 项目初始化 | 开发者 | Next.js项目 |
| 数据库设计 | 开发者 | Prisma Schema |
| 认证系统 | 开发者 | 登录/注册 |
| 基础UI | 开发者 | 首页/Dashboard |

#### 第2周：核心功能

| 任务 | 负责人 | 产出 |
|------|-------|------|
| 空投爬虫 | 开发者 | Twitter/Discord爬虫 |
| 数据处理 | 开发者 | 去重/评分算法 |
| 项目展示页 | 开发者 | 项目列表/详情页 |
| 搜索功能 | 开发者 | 关键词搜索 |

#### 第3周：用户系统

| 任务 | 负责人 | 产出 |
|------|-------|------|
| 订阅系统 | 开发者 | 套餐管理 |
| 激活码系统 | 开发者 | 生成/验证 |
| 支付集成 | 开发者 | 支付宝/微信 |
| 偏好设置 | 开发者 | 推送偏好 |

#### 第4周：推送功能

| 任务 | 负责人 | 产出 |
|------|-------|------|
| WebSocket | 开发者 | 实时推送 |
| 邮件推送 | 开发者 | SMTP集成 |
| Telegram推送 | 开发者 | Bot API |
| 推送模板 | 内容运营 | 消息模板 |

#### 第5-6周：测试优化

| 任务 | 负责人 | 产出 |
|------|-------|------|
| 内部测试 | 全体 | Bug修复 |
| 用户测试 | 种子用户 | 反馈收集 |
| 性能优化 | 开发者 | 速度优化 |
| 上线准备 | 全体 | 部署/监控 |

### 4.2 桌面端 (Electron)

**开发周期：** 6-8周

| 阶段 | 任务 | 产出 |
|------|------|------|
| 第1周 | Electron框架 | 基础应用 |
| 第2周 | 系统托盘 | 后台运行 |
| 第3周 | 本地爬虫 | 24小时监控 |
| 第4周 | 推送集成 | 桌面通知 |
| 第5周 | 自动更新 | 版本管理 |
| 第6周 | 测试优化 | Bug修复 |

---

## 五、运营策略

### 5.1 定价策略

**初始定价（试水期）**

| 套餐 | 价格 | 策略 |
|------|------|------|
| 体验卡 | ¥9.9 | 7天，低门槛转化 |
| 月卡 | ¥29 | 比竞品低30% |
| 季卡 | ¥79 | 省¥8 (9%off) |
| 年卡 | ¥199 | 省¥149 (43%off) |
| 终身卡 | ¥499 | 限量发售 |

**策略说明：**
1. **体验卡低价** - 降低尝试门槛
2. **月卡微利** - 快速获得用户
3. **年卡促销** - 锁定长期用户
4. **终身卡限量** - 早期用户福利

### 5.2 激活码运营

**生成策略：**
| 场景 | 数量 | 用途 |
|------|------|------|
| 预售期 | 100张 | 种子用户赠送 |
| 推广期 | 500张 | KOL赠送 |
| 活动期 | 200张 | 抽奖/活动 |

**销售渠道：**
1. 官网直接购买
2. 淘宝/闲鱼分销
3. 加密社群合作
4. KOL推广

### 5.3 推广策略

**冷启动：**
| 渠道 | 策略 | 预期 |
|------|------|------|
| Telegram | 价值内容输出 | 500-1000用户 |
| Twitter | 产品更新动态 | 300-500粉丝 |
| 加密社群 | 经验分享+引流 | 200-500用户 |
| Product Hunt | 发布日推广 | 500-1000访问 |

**增长期：**
| 渠道 | 策略 | 预期 |
|------|------|------|
| 付费推广 | KOL合作 | 1000-5000用户 |
| 内容营销 | SEO/博客 | 持续增长 |
| 口碑传播 | 用户推荐 | 20%新用户 |
| 合作共赢 | 项目方合作 | 精准用户 |

---

## 六、财务预测

### 6.1 成本结构

| 项目 | 月费用 | 说明 |
|------|-------|------|
| 服务器 | ¥500-2000 | Vercel + VPS |
| 数据库 | ¥200-500 | PostgreSQL |
| 第三方API | ¥0-500 | 视使用量 |
| 域名/SSL | ¥50-100 | 域名年费 |
| **总计** | **¥750-3100/月** | **低成本运营** |

### 6.2 收入预测

| 阶段 | 时间 | 付费用户 | 月收入 |
|------|------|---------|-------|
| MVP上线 | 0-1月 | 10-50 | ¥500-2000 |
| 增长期 | 1-3月 | 50-200 | ¥3K-10K |
| 发展期 | 3-6月 | 200-500 | ¥10K-30K |
| 成熟期 | 6-12月 | 500-2000 | ¥50K-200K |

### 6.3 盈亏平衡

| 指标 | 数值 |
|------|------|
| 固定成本 | ¥3000/月 |
| 目标用户 | 100付费用户 |
| 平均客单价 | ¥50/月 |
| **平衡点** | **60付费用户** |

---

## 七、项目文件

**项目文档位置：**
```
~/openclaw/workspace/projects/airdrop-intelligence-pro/
├── PROJECT.md              # 本文档
├── ARCHITECTURE.md         # 详细技术架构
├── API.md                  # API接口文档
├── DATABASE.md             # 数据库设计文档
├── DEVELOPMENT.md          # 开发规范
└── DEPLOYMENT.md          # 部署文档
```

---

## 八、下一步行动

### 立即执行

1. ✅ 产品设计文档 - 完成
2. ⏳ 技术选型确认
3. ⏳ 开发计划制定
4. ⏳ 开始开发

### 待确认事项

1. 定价是否合理？
2. 功能优先级是否正确？
3. 开发周期是否可行？
4. 还有什么遗漏？

---

**产品设计文档 v1.0**
**创建时间：** 2026-02-07
**版本号：** 1.0.0

---

**Let's Build This! 🚀**
