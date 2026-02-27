#!/usr/bin/env python3
"""
持仓实时价格 - 使用腾讯接口
绕过代理问题
"""
import os
import requests

# 清除代理设置
for k in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
    os.environ.pop(k, None)

# 创建不使用代理的session
session = requests.Session()
session.trust_env = False

# 持仓
positions = {
    '300861': {'shares': 1073, 'avg': 18.63, 'name': '美畅股份'},
    '300719': {'shares': 766, 'avg': 20.89, 'name': '安达维尔'},
    '300678': {'shares': 376, 'avg': 34.01, 'name': '中科信息'},
    '300875': {'shares': 235, 'avg': 43.46, 'name': '捷强装备'},
    '000428': {'shares': 2108, 'avg': 3.89, 'name': '华天酒店'},
}

print('=== 实时盈亏 ===\n')

total_pnl = 0
for symbol, info in positions.items():
    # 腾讯接口格式
    # 6开头是上海(sh), 0/3开头是深圳(sz)
    if symbol.startswith('6'):
        code = f'sh{symbol}'
    else:
        code = f'sz{symbol}'
    
    url = f'https://qt.gtimg.cn/q={code}'
    
    try:
        r = session.get(url, timeout=5)
        data = r.text.strip()
        
        # 解析: v_sz300861="51~美畅股份~300861~18.87~..."
        if data.startswith('v_'):
            # 去掉前缀和引号
            data = data.split('=')[1].strip('"')
            parts = data.split('~')
            
            # 格式: 51~名称~代码~价格~...
            if len(parts) >= 4:
                name = parts[1]
                price = float(parts[3])
                pct = float(parts[4]) / 100 if parts[4] else 0
            
            shares = info['shares']
            avg = info['avg']
            pnl = (price - avg) * shares
            pnl_pct = (price - avg) / avg * 100
            total_pnl += pnl
            
            print(f'{symbol} {name}')
            print(f'  现价¥{price:.2f} ({pct:+.2f}%) 成本¥{avg:.2f}')
            print(f'  盈亏 ¥{pnl:+,.0f} ({pnl_pct:+.1f}%)')
            print()
    except Exception as e:
        print(f'{symbol}: 获取失败 ({e})\n')

print('='*35)
print(f'总盈亏: ¥{total_pnl:+,.0f}')
print(f'总资产: ¥{100000+total_pnl:,.0f}')
print(f'现金: ¥32,807')
print('='*35)
