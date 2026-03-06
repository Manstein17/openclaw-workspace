# Web Scraping Skill for Stock Data

## 概述

这个Skill提供网页抓取功能，用于获取A股股票数据。

## 注意事项 ⚠️

1. **遵守规则** - 查看网站的robots.txt
2. **控制频率** - 请求间隔≥3秒，避免被封IP
3. **使用代理** - 可配置代理池避免被识别
4. **法律风险** - 仅用于个人学习，不要传播抓取数据
5. **缓存优先** - 优先使用API数据，抓取作为补充

---

## 核心功能

### 1. 新浪财经K线抓取

```python
from scraping import SinaScraper

scraper = SinaScraper()
data = scraper.get_kline('600000', days=30)
```

### 2. 东财实时行情抓取

```python
from scraping import EastMoneyScraper

scraper = EastMoneyScraper()
price = scraper.get_realtime('600000')
```

### 3. 财经新闻抓取

```python
from scraping import NewsScraper

scraper = NewsScraper()
news = scraper.get_stock_news('600000')
```

---

## 配置

### 代理配置（可选）

```python
import os
os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'
```

### 请求间隔

```python
REQUEST_DELAY = 3  # 每次请求间隔3秒
MAX_RETRIES = 3    # 最多重试3次
```

---

## 文件结构

```
~/.openclaw/workspace/
└── scraping/
    ├── __init__.py
    ├── base.py       # 基类
    ├── sina.py      # 新浪财经
    ├── eastmoney.py # 东方财富
    └── news.py      # 财经新闻
```

---

## 使用示例

### 获取K线数据

```python
from scraping.sina import SinaKline

sina = SinaKline()
klines = sina.get('sh600000', limit=30)

for k in klines:
    print(f"{k['date']}: {k['close']}")
```

### 获取实时价格

```python
from scraping.eastmoney import EastMoneyRealtime

em = EastMoneyRealtime()
price = em.get('sh600000')

print(f"现价: {price['price']}")
print(f"涨跌: {price['change_pct']}%")
```

---

## 风险控制

| 措施 | 说明 |
|------|------|
| 请求间隔 | ≥3秒/请求 |
| 重试机制 | 最多3次 |
| 超时设置 | 10秒超时 |
| 错误处理 | 详细日志记录 |
| 代理支持 | 可配置代理 |

---

## 维护

- 定期检查网站结构是否变化
- 更新选择器以适应页面变化
- 监控抓取成功率
