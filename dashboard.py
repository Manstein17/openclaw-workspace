#!/usr/bin/env python3
"""
决策仪表盘
显示交易系统当前状态的简洁面板
"""
import os
import sys
import json
import requests
from datetime import datetime

# 禁用代理
for k in ['http_proxy', 'https_proxy']:
    os.environ.pop(k, None)

class DecisionDashboard:
    """决策仪表盘"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
    
    def get_price(self, sym):
        """获取实时价格"""
        try:
            code = f'sh{sym}' if sym.startswith('6') or sym.startswith('9') else f'sz{sym}'
            r = self.session.get(f'https://qt.gtimg.cn/q={code}', timeout=5)
            if 'v_' in r.text:
                parts = r.text.split('=')[1].split('~')
                price = float(parts[3]) if parts[3] else 0
                prev = float(parts[4]) if parts[4] else price
                pct = (price - prev) / prev * 100 if prev else 0
                return {'price': price, 'pct': pct}
        except:
            pass
        return {'price': 0, 'pct': 0}
    
    def load_portfolio(self):
        """加载持仓"""
        path = os.path.expanduser('~/.openclaw/workspace/simulations/portfolio.json')
        with open(path) as f:
            return json.load(f)
    
    def render(self):
        """渲染仪表盘"""
        p = self.load_portfolio()
        
        cash = p.get('cash', 0)
        positions = p.get('positions', {})
        initial = 10000
        
        # 计算总盈亏
        total_pnl = 0
        position_list = []
        
        for sym, pos in positions.items():
            data = self.get_price(sym)
            curr = data.get('price', pos.get('avg_price', 0))
            avg = pos.get('avg_price', 0)
            pnl = (curr - avg) * pos.get('shares', 0)
            total_pnl += pnl
            
            position_list.append({
                'symbol': sym,
                'current': curr,
                'avg': avg,
                'pnl': pnl,
                'pct': data.get('pct', 0),
                'shares': pos.get('shares', 0)
            })
        
        total_value = cash + sum(x['current'] * x['shares'] for x in position_list)
        pnl_pct = (total_pnl / initial) * 100 if initial else 0
        
        # 渲染
        lines = []
        lines.append("┌" + "─" * 50 + "┐")
        lines.append("│" + " 📊 决策仪表盘 ".center(50) + "│")
        lines.append("├" + "─" * 50 + "┤")
        
        # 账户状态
        emoji = "🟢" if total_pnl >= 0 else "🔴"
        lines.append(f"│ 💰 总资产: ¥{total_value:,.0f}  {emoji} {pnl_pct:+.1f}%".ljust(51) + "│")
        lines.append(f"│ 💵 现金: ¥{cash:,.0f}  (持仓{len(positions)}只)".ljust(51) + "│")
        
        if position_list:
            lines.append("├" + "─" * 50 + "┤")
            lines.append("│ 📈 持仓状态".ljust(51) + "│")
            
            # 按盈亏排序
            position_list.sort(key=lambda x: x['pnl'], reverse=True)
            
            for i, pos in enumerate(position_list, 1):
                emoji = "🟢" if pos['pnl'] >= 0 else "🔴"
                status = "✅" if pos['pnl'] >= 0 else "⚠️"
                
                if pos['pct'] >= 15:
                    action = "🎯止盈"
                elif pos['pct'] <= -5:
                    action = "🔴止损"
                elif pos['pct'] >= 8:
                    action = "⏸️半仓"
                else:
                    action = "持有"
                
                line = f"│ {i}. {pos['symbol']} ¥{pos['current']:.2f} {emoji}{pos['pnl']:+,.0f} {action}".ljust(51)
                lines.append(line + "│")
        
        # 底部
        lines.append("├" + "─" * 50 + "┤")
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        lines.append("│ " + f"🕐 更新时间: {now}".ljust(50) + "│")
        lines.append("└" + "─" * 50 + "┘")
        
        return '\n'.join(lines)


if __name__ == '__main__':
    dashboard = DecisionDashboard()
    print(dashboard.render())
