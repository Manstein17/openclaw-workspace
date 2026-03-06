# 交易系统更新日志

## 2026-03-01

### 新增功能

1. **交易报告** - trading_report.py
   - 每日交易总结
   - 持仓分析
   - 盈亏统计

2. **智能更新** - smart_update_v2.py
   - 批量更新股票数据
   - 增量获取机制

3. **批量更新** - batch_update.py
   - 多线程并行获取
   - 速率限制保护

4. **谨慎更新** - careful_update.py
   - 验证数据完整性
   - 错误重试机制

### 问题修复

1. **Python命令** - 创建 symlink 解决 python 命令不存在问题
   - 位置: ~/.local/bin/python -> /opt/homebrew/bin/python3

---

## 2026-02-28

### 新增功能

1. **LLM分析器** - llm_analyzer.py
   - 混合传统公式 + LLM分析
   - 分析数据汇总
   - 通过OpenClaw会话让LLM分析

2. **东财API集成** - fund_flow.py
   - 真实主力资金数据
   - 大单/中单/小单净流入
   - 东财优先，估算备选

3. **网络助手** - network_helper.py
   - 解决VPN代理问题
   - 金融API直连

4. **实时新闻** - realtime_news.py
   - 新浪财经实时新闻
   - 自动过滤财经相关内容

5. **开发助手** - 调用ACXP协助开发

6. **自动推送更新** - Discord线程

### 问题修复

- 日志输出使用 unbuffered 模式

---

## 2026-02-27

### 策略参数调整

| 参数 | 修改前 | 修改后 |
|------|---------|---------|
| 持仓上限 | 5只 | 3只 |
| 买入评分 | ≥65分 | ≥60分 |
| 资金流向 | 无限制 | ≥0 |

### 数据源

- 腾讯实时 ✅
- 新浪历史 ✅ (香港节点)
- 东财 ❌ (被VPN阻断)

---

## 系统架构

```
realtime_trader.py (主系统)
├── lean_strategies.py (20个策略)
├── fund_flow.py (资金流向)
├── market_heat.py (市场热度)
├── auto_policy.py (政策分析)
├── trading_journal.py (交易日志)
└── snowball_sim.py (模拟交易)
```

---

## 策略列表 (20个)

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

## 买入逻辑

1. 随机选800只股票
2. 排除已持仓
3. 排除非主线板块
4. 技术分析评分
5. 20策略信号 + 回测验证
6. 资金流向检查
7. 行业调整
8. 综合评分≥60分 → 买入

---

## 卖出逻辑

- 止损: -5%
- 止盈1: +8% (卖一半)
- 止盈2: +15% (全卖)
