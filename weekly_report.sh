#!/bin/bash
# 每周复盘报告生成
# 运行: python weekly_report.py

cd /Users/manstein17/.openclaw/workspace
source venv/bin/activate

python3 -c "
from trading_journal import TradingJournal
from weekly_analyzer import WeeklyAnalyzer

print('='*60)
print('📊 交易系统周报')
print('='*60)

# 每日报告
journal = TradingJournal()
print(journal.generate_daily_report())

# 周报
analyzer = WeeklyAnalyzer()
print(analyzer.generate_report())

# 保存周报
analyzer.save_report()
print('周报已保存')
"
