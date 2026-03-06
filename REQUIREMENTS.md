# 交易系统改进需求文档

## 项目概述

- **项目名称**: A股量化交易系统
- **语言**: Python
- **目标**: 实现专业级量化交易系统

---

## 当前系统架构

```
realtime_trader.py    # 主系统 (500+行)
├── lean_strategies.py  # 20个量化策略
├── fund_flow.py       # 资金流向分析
├── market_heat.py    # 市场热度分析
├── auto_policy.py    # 政策分析
├── snowball_sim.py   # 模拟交易
├── daily_update.py   # 数据更新
└── check_positions.py # 持仓查询
```

---

## 核心功能

### 1. 选股系统
- 随机抽取800只股票进行分析
- 综合评分系统 (满分120+)
- 20个策略信号 + 回测验证
- 行业/板块筛选

### 2. 买入逻辑
- 评分 ≥ 60分
- 资金流向 ≥ 0
- 持仓上限 3只
- 每次20%仓位

### 3. 卖出逻辑
- 止损: -5%
- 止盈1: +8% (卖一半)
- 止盈2: +15% (全卖)

### 4. 数据源
- 腾讯实时行情 (可用)
- 新浪历史K线 (可用)
- 东财资金流向 (当前被VPN阻断)

---

## 待改进问题

### 问题1: 日志不透明
**现状**: 运行日志只有 "DataSource initialized"，看不到分析过程
**期望**: 看到完整的选股/评分/决策过程

### 问题2: 东财API无法使用
**现状**: VPN代理阻断东财API
**期望**: 
- 方案A: 在Shadowrocket添加绕过规则
- 方案B: 使用其他数据源替代

### 问题3: 资金流向不准确
**现状**: 使用估算模式，准确率约30%
**期望**: 获取真实主力净流入数据

### 问题4: 策略评分优化
**现状**: 评分体系较简单
**期望**: 
- 策略加权优化
- 增加更多技术指标
- 回测参数调优

---

## 20个策略列表

| 类别 | 策略 |
|------|------|
| 均线交叉 | MA5_10, MA10_20, MA20_50 |
| 趋势 | MACD, PSAR, ICHIMOKU |
| 动量 | MOM, MOM5, MOM12, RSI, STOCH, CCI |
| 突破 | BRK10, BRK20, VOLBRK |
| 布林带 | BB |
| 均值回归 | MR |
| 通道 | DC, KC |
| 复合 | COMPOSITE |

---

## 评分体系

| 指标 | 分数 |
|------|------|
| 基础分 | 50 |
| 支撑位 | +15 |
| 均线多头 | +10 |
| 策略信号 | +5/个 |
| 资金流向 | ±10~20 |
| 行业热度 | +20 |
| 胜率加分 | +胜率×20 |

---

## 文件位置

```
工作目录: ~/.openclaw/workspace/
股票数据: ~/.openclaw/workspace/stock_cache/daily/
交易日志: ~/.openclaw/workspace/realtime_trading.log
持仓数据: ~/.openclaw/workspace/simulations/portfolio.json
```

---

## 改进优先级

1. **高优先级**: 修复日志输出
2. **高优先级**: 解决东财API问题
3. **中优先级**: 优化策略评分
4. **低优先级**: 增加更多策略

---

## 技术要求

- Python 3.14
- 依赖: akshare, efinance, pandas, requests
- 数据更新速率: 新浪API约1.5次/秒

---

## 联系方式

- 系统运行命令: `python realtime_trader.py`
- 数据更新: `python daily_update.py`
