# 金融API防爬机制与应对策略

> 更新日期: 2026-03-04

---

## 1. 新浪财经 API

### 防爬规则

| 项目 | 说明 |
|------|------|
| **限速代码** | 456错误 "Kinsoku jikou desu!" |
| **限制方式** | 按小时/天计算请求次数 |
| **触发条件** | 短时间大量请求 |
| **User-Agent** | 需要真实浏览器UA |

### 应对策略

```python
# 推荐配置
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://finance.sina.com.cn/'
}
# 请求间隔: ≥3-5秒
# 缓存时间: 5-10分钟
```

---

## 2. 东方财富 API

### 防爬规则

| 项目 | 说明 |
|------|------|
| **限制方式** | 每秒/每分钟请求数 |
| **封禁机制** | 同IP频繁请求自动封禁 |
| **检测方式** | 请求频率 + 来源IP + Cookie |
| **可选** | 需要API Key (付费版) |

### 应对策略

```python
# 推荐配置
session.headers.update({
    'User-Agent': 'Mozilla/5.0',
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9',
})
# 请求间隔: ≥2-3秒
# 失败等待: 30-60秒
# 使用缓存减少请求
```

---

## 3. 腾讯API

### 防爬规则

| 项目 | 说明 |
|------|------|
| **限制方式** | 需要Cookie/Referer |
| **错误信息** | "Can't load controller" |
| **检测方式** | 请求头完整性 |

### 应对策略

```python
# 推荐配置
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://finance.qq.com/',
    'Accept': '*/*',
}
# 请求间隔: ≥2秒
```

---

## 4. 通用策略

### 请求间隔配置

| 场景 | 间隔 |
|------|------|
| 正常请求 | 3-5秒 |
| 被限速后 | 60-120秒 |
| 批量更新 | 2-3秒 |

### 请求头模板

```python
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
```

### 重试机制

```python
MAX_RETRIES = 3
RETRY_DELAY = 60  # 被限速后等待60秒
RETRY_BACKOFF = 2  # 指数退避
```

---

## 5. 文件位置

```
~/.openclaw/workspace/
├── scraping/
│   ├── base.py          # 基类 (已配置UA和间隔)
│   ├── sina.py         # 新浪 (已优化)
│   └── eastmoney.py    # 东财 (已优化)
├── realtime_trader.py  # 交易系统
└── data_health_monitor.py  # 数据健康检查
```

---

## 6. 监控指标

| 指标 | 阈值 |
|------|------|
| 成功率 | >95% |
| 456错误 | <5% |
| 响应时间 | <5秒 |

---

*持续更新中...*
