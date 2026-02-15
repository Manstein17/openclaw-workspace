# ZeroClaw 安卓部署指南 (2026)

> 通过 Termux 在安卓手机上运行 ZeroClaw

---

## 环境要求

- **安卓设备**: Android 10 或更高
- **Termux**: 从 F-Droid 安装（非 Google Play）
- **API Key**: 使用任何 ZeroClaw 支持的 API（OpenAI、Anthropic、MiniMax 等）

---

## 步骤 1: 安装 Termux

从 F-Droid 下载并安装 Termux：
https://f-droid.org/packages/com.termux/

---

## 步骤 2: 安装 Rust 和 ZeroClaw

```bash
# 更新
pkg update && pkg upgrade -y

# 安装 Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# 克隆 ZeroClaw
git clone https://github.com/theonlyhennygod/zeroclaw.git
cd zeroclaw

# 编译（首次约 10 分钟）
cargo build --release

# 安装
cargo install --path . --force
```

---

## 步骤 3: 初始化

```bash
# 快速设置（无需交互）
zeroclaw onboard --api-key sk-你的API密钥 --provider openrouter

# 或交互式向导
zeroclaw onboard --interactive
```

⚠️ **重要**：Gateway Bind 选择 **Loopback (127.0.0.1)**

---

## 步骤 4: 启动

```bash
# 启动 Gateway
zeroclaw gateway

# 或后台运行
zeroclaw daemon
```

---

## 验证命令

- `/status` - 检查状态
- `/reset` - 重置会话

---

## 访问 Dashboard

手机浏览器访问：
```
http://127.0.0.1:8080
```

获取 Token：
```bash
zeroclaw config get gateway.auth.token
```

---

## ZeroClaw 优势（对比 OpenClaw）

| 指标 | ZeroClaw | OpenClaw |
|------|----------|----------|
| 内存 | ~7.8 MB | ~1.5 GB |
| 大小 | 3.4 MB | 28 MB |
| 启动 | <10ms | ~1s |

---

## Pro 技巧

### 保持运行
```bash
termux-wake-lock
```
设置中禁用 Termux 电池优化。

---

## 常见问题

| 问题 | 解决方法 |
|------|----------|
| 编译失败 | 确保 Rust 已正确安装 |
| 无法连接 | 检查 Gateway Bind 是否为 127.0.0.1 |

---

*文档创建时间: 2026-02-15*
