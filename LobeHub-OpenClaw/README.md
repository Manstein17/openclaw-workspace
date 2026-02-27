# LobeHub-OpenClaw

> LobeHub 与 OpenClaw 系统架构级整合方案

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

## 📋 目录

- [✨ 特性](#-特性)
- [🎯 整合优势](#-整合优势)
- [🏗️ 架构设计](#️-架构设计)
- [📦 功能模块](#-功能模块)
- [🚀 快速开始](#-快速开始)
- [⚙️ 配置指南](#️-配置指南)
- [📚 文档](#-文档)
- [🤝 贡献](#-贡献)
- [📄 许可证](#-许可证)

## ✨ 特性

- 🔗 **架构解耦** - Core Layer + Adapter Layer 分离，易于跟随上游更新
- 🧠 **记忆互通** - LobeHub 与 OpenClaw 共享统一记忆系统
- 🛠️ **Skills 共享** - 两边 Skills 可互相调用、转换
- ⚡ **事件驱动** - 跨平台事件触发与响应
- 🌐 **统一接口** - 统一模型调用、记忆操作、事件总线

## 🎯 整合优势

### 对比整合前后

| 能力 | 整合前 | 整合后 |
|------|--------|--------|
| **模型选择** | 各自独立 | 统一接口，任意切换 |
| **记忆管理** | 分散、不可搜索 | 集中、语义搜索 |
| **自动化** | OpenClaw 独有 | 两边都可触发 |
| **UI 操作** | LobeHub 独有 | 两边都可操作 |
| **Skills** | 互不兼容 | 共享、互转 |

### 核心优势

1. **消除信息孤岛**
   - LobeHub 对话 → 自动记录到 OpenClaw 记忆
   - OpenClaw 任务 → 可视化展示在 LobeHub

2. **能力互补**
   ```
   LobeHub = UI 工作台（视觉、对话、调试）
   OpenClaw = 自动化引擎（定时、任务、记忆）
   ```

3. **成本优化**
   - 共享 API Key 配置
   - 统一模型调用（不重复付费）
   - 集中记忆管理（减少 token 消耗）

4. **扩展性强**
   - 新增平台只需写 Adapter
   - Core Layer 保持稳定

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层                                     │
│            Telegram / LobeHub UI / CLI / API                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                       核心抽象层 (Core Layer)                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐       │
│  │   Model     │  │   Memory    │  │      Event Bus      │       │
│  │ Interface   │  │   Interface │  │                     │       │
│  └─────────────┘  └─────────────┘  └─────────────────────┘       │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                  Skill Registry                         │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
┌─────────▼─────────┐           ┌─────────▼─────────┐
│    LobeHub        │           │    OpenClaw       │
│                   │    ◄──►   │                   │
│  • UI 操作        │           │  • 自动化         │
│  • 视觉分析       │           │  • 定时任务       │
│  • Prompt 调试    │           │  • Telegram 推送   │
│  • 模型市场       │           │  • 记忆持久化     │
└───────────────────┘           └───────────────────┘
          │                               │
└─────────┴───────────────────────────────┴─────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      适配器层 (Adapter Layer)                    │
│  ┌───────────────────┐          ┌───────────────────────────┐    │
│  │  LobeHub Adapter  │          │   OpenClaw Adapter        │    │
│  │                   │          │                            │    │
│  │ • OpenAI 兼容 API │          │   • Gateway RPC           │    │
│  │ • WebSocket 实时  │          │   • Session 管理           │    │
│  │ • Agent 市场      │          │   • Cron 任务              │    │
│  └───────────────────┘          └───────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 核心原则

| 原则 | 说明 |
|------|------|
| **依赖倒置** | 上层依赖抽象，不依赖具体实现 |
| **开闭原则** | 新增平台只需添加 Adapter |
| **单一职责** | 每个模块只做一件事 |
| **可替换** | 可单独使用任一 Adapter |

## 📦 功能模块

### 1. 统一模型接口 (Core Model)

支持多个模型提供商的统一调用：

```typescript
import { ModelAdapter, OpenAIAdapter, AnthropicAdapter, LobeHubAdapter } from './core/model';

// 创建适配器
const openai = new OpenAIAdapter({ model: 'gpt-4' });
const anthropic = new AnthropicAdapter({ model: 'claude-sonnet-4' });
const lobehub = new LobeHubAdapter({ baseUrl: 'http://localhost:3210' });

// 统一调用
const response = await adapter.chat([
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'Hello!' }
]);
```

**支持的功能：**
- ✅ 同步/流式调用
- ✅ 模型列表获取
- ✅ 健康检查
- ✅ 多模态支持（图片）

### 2. 统一记忆系统 (Core Memory)

多种记忆存储后端：

```typescript
import { MemoryAdapter, MarkdownMemoryAdapter, QdrantMemoryAdapter } from './core/memory';

// Markdown 文件存储（与 OpenClaw 兼容）
const markdown = new MarkdownMemoryAdapter({ memoryDir: './memory' });

// Qdrant 向量搜索（语义检索）
const qdrant = new QdrantMemoryAdapter({ 
  url: 'http://localhost:6333',
  collectionName: 'lobehub-openclaw'
});

// 使用统一接口
await markdown.add({
  content: '用户偏好中文回复',
  priority: 'P0',
  tags: ['preference'],
  source: 'user'
});

const result = await markdown.search({ query: '用户偏好' });
```

**记忆优先级：**
| 优先级 | 说明 | 淘汰周期 |
|--------|------|----------|
| **P0** | 核心记忆（身份、偏好、安全红线） | 永不淘汰 |
| **P1** | 阶段记忆（当前项目、策略决策） | 90 天 |
| **P2** | 临时记忆（一次性事件、调试记录） | 30 天 |

### 3. 事件总线 (Core Event)

跨平台事件驱动：

```typescript
import { EventBus, Events } from './core/event';

const bus = new EventBus();

// 订阅事件
bus.subscribe(Events.LobeHub.CHAT_COMPLETE, async (event) => {
  console.log('LobeHub 对话完成:', event.payload);
});

// 发布事件
await bus.publish({
  type: 'custom:event',
  source: 'my-app',
  payload: { data: 'test' }
});

// 预定义事件类型
const Events = {
  LobeHub: {
    CHAT_COMPLETE: 'lobehub:chat.complete',
    AGENT_CREATED: 'lobehub:agent.created',
    PROMPT_EXPORTED: 'lobehub:prompt.exported',
  },
  OpenClaw: {
    TASK_COMPLETE: 'openclaw:task.complete',
    MEMORY_UPDATED: 'openclaw:memory.updated',
    CRON_TRIGGERED: 'openclaw:cron.triggered',
  }
};
```

### 4. 共享记忆 (Shared Memory)

双向记忆同步：

```typescript
import { SharedMemoryIntegration } from './integrations/shared-memory';

const shared = new SharedMemoryIntegration({
  adapter: markdown,
  lobehubDir: './lobehub-memory',
  openclawDir: './openclaw-memory',
  autoSync: true,
  syncInterval: 60000
}, eventBus);

// 启动
shared.start();

// 手动同步
await shared.sync();

// 导入 LobeHub 记忆
await shared.importFromLobeHub(entries);

// 导入 OpenClaw 记忆
await shared.importFromOpenClaw(entries);

// 搜索（跨平台）
const results = await shared.search('BTC 监控', {
  source: 'all',
  limit: 10
});
```

### 5. 共享 Skills (Shared Skills)

Skills 互通与转换：

```typescript
import { SharedSkillsIntegration } from './integrations/shared-skills';

const skills = new SharedSkillsIntegration({
  lobehubSkillsDir: './lobehub-skills',
  openclawSkillsDir: './openclaw-skills',
  sharedDir: './shared-skills',
  autoImport: true,
}, eventBus);

// 初始化
await skills.init();

// 导入所有
await skills.importAll();

// 执行 Skill
const result = await skills.execute('btc-monitor', {
  interval: '1h',
  threshold: 50000
});

// 查找 Skills
const found = skills.find({
  tags: ['crypto', 'monitor'],
  source: 'all'
});

// 格式转换
const lobehubFormat = await skills.exportToLobeHubFormat('skill-id');
const openclawFormat = await skills.exportToOpenClawFormat('skill-id');
```

### 6. 跨平台触发 (Cross Trigger)

事件驱动自动化：

```typescript
import { CrossTriggerIntegration } from './integrations/cross-trigger';

const trigger = new CrossTriggerIntegration({
  lobehubWsUrl: 'ws://localhost:3210/ws',
  openclawGatewayUrl: 'http://localhost:18789',
  autoConnect: true,
}, eventBus, openclaw, lobehub);

// 初始化
await trigger.init();

// 手动触发
await trigger.triggerOpenClawFromLobeHub({
  prompt: '分析 BTC 行情并发送报告',
  channel: 'telegram'
});

// 添加触发规则
trigger.addRule({
  name: 'LobeHub Chat → OpenClaw Memory',
  enabled: true,
  condition: {
    platform: 'lobehub',
    event: 'chat.complete'
  },
  action: {
    platform: 'openclaw',
    type: 'log_memory',
    params: {}
  }
});

// 获取状态
const status = trigger.getStatus();
```

## 🚀 快速开始

### 安装

```bash
git clone https://github.com/Manstein17/LobeHub-OpenClaw.git
cd LobeHub-OpenClaw
npm install
```

### 环境配置

创建 `.env` 文件：

```env
# OpenClaw
OPENCLAW_GATEWAY_URL=http://localhost:18789
OPENCLAW_WORKSPACE=/path/to/openclaw-workspace

# LobeHub
LOBEHUB_URL=http://localhost:3210
LOBEHUB_WS_URL=ws://localhost:3210/ws

# Qdrant (可选，向量搜索)
QDRANT_URL=http://localhost:6333

# API Keys (可选，如果需要调用 API)
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
```

### 基础使用

```typescript
import { LobeHubOpenClaw } from './src';

async function main() {
  // 创建系统实例
  const system = await LobeHubOpenClaw.create({
    openclaw: {
      gatewayUrl: process.env.OPENCLAW_GATEWAY_URL!,
      workspaceDir: process.env.OPENCLAW_WORKSPACE!,
    },
    lobehub: {
      baseUrl: process.env.LOBEHUB_URL!,
    },
    integrations: {
      sharedMemory: true,
      sharedSkills: true,
      crossTrigger: true,
    },
  });

  // 检查状态
  const status = await system.status();
  console.log('System status:', status);

  // 聊天
  const response = await system.lobehub.chat({
    messages: [{ role: 'user', content: 'Hello!' }]
  });
  console.log('Response:', response);

  // 记忆搜索
  const memories = await system.sharedMemory?.search('用户偏好');
  console.log('Memories:', memories);
}

main().catch(console.error);
```

### 运行

```bash
# 开发模式
npm run dev

# 构建
npm run build

# 测试
npm test
```

## ⚙️ 配置指南

### 完整配置项

```typescript
interface LobeHubOpenClawConfig {
  // OpenClaw 配置
  openclaw?: {
    gatewayUrl: string;      // Gateway 地址
    workspaceDir: string;     // 工作目录
  };
  
  // LobeHub 配置
  lobehub?: {
    baseUrl: string;         // API 地址
    apiKey?: string;         // API Key
  };
  
  // 记忆配置
  memory?: {
    type: 'markdown' | 'qdrant' | 'memos';
    dir?: string;            // 存储目录
  };
  
  // 整合模块
  integrations?: {
    sharedMemory?: boolean;   // 启用记忆共享
    sharedSkills?: boolean;  // 启用 Skills 共享
    crossTrigger?: boolean;  // 启用跨平台触发
  };
}
```

### 目录结构建议

```
project/
├── lobehub-openclaw/       # 本项目
├── workspace/              # OpenClaw 工作区
│   ├── memory/
│   ├── skills/
│   └── config/
├── lobehub-data/           # LobeHub 数据
│   ├── memory/
│   └── agents/
└── shared/                 # 共享数据
    ├── memory/
    ├── skills/
    └── triggers/
```

### 记忆文件格式

与 OpenClaw 兼容的 Markdown 格式：

```markdown
---
id: xxx
priority: P1
created: 2026-02-11T10:00:00Z
updated: 2026-02-11T10:00:00Z
tags: crypto, btc
source: openclaw
---

# BTC 监控配置

- [P1][2026-02-11] 每小时监控 BTC 价格
- [P1][2026-02-11] 阈值: $50,000
- [P2][2026-02-11] 上次检查正常
```

### Skills 格式

```typescript
interface SkillManifest {
  id: string;           // 唯一标识
  name: string;        // 名称
  version: string;     // 版本
  description: string; // 描述
  tags: string[];      // 标签
  parameters: any[];   // 参数定义
  output: {
    type: 'text' | 'json' | 'file';
    description: string;
  };
  source: 'lobehub' | 'openclaw' | 'custom';
  timeout?: number;    // 超时(ms)
  retries?: number;    // 重试次数
}
```

## 📚 文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api/)
- [更新策略](docs/update-strategy.md)
- [开发日志](docs/)

## 🔄 更新跟随策略

本项目使用 Git Subtree 跟随上游：

```bash
# 更新 OpenClaw
git subtree pull --prefix=adapters/openclaw-adapter \
  https://github.com/openclaw/openclaw.git main

# 更新 LobeHub
git subtree pull --prefix=adapters/lobehub-adapter \
  https://github.com/lobehub/lobehub.git main
```

### 兼容性

| 组件 | 版本要求 |
|------|----------|
| Node.js | >= 18.0.0 |
| TypeScript | >= 5.0 |
| OpenClaw | >= 2026.2.0 |
| LobeHub | >= 0.x |

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 创建 Pull Request

## 📄 许可证

MIT License - see [LICENSE](LICENSE) 文件

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) - 本地 AI Agent 框架
- [LobeHub](https://github.com/lobehub/lobehub) - AI 工作空间
- [Qdrant](https://github.com/qdrant/qdrant) - 向量数据库

---

**Stars & Issues 欢迎！** ⭐

如果这个项目对你有帮助，请给它一个 Star！
