#!/usr/bin/env python3
"""交易报告生成器 - 详细模板"""
import os, json, requests
from datetime import datetime
from trading_system_final import DataSource
from lean_strategies import get_all_strategies

class TradingReport:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.ds = DataSource()
        self.strategies = get_all_strategies()
    
    def get_price(self, sym):
        try:
            code = f'sh{sym}' if sym.startswith('6') or sym.startswith('9') else f'sz{sym}'
            r = self.session.get(f'https://qt.gtimg.cn/q={code}', timeout=5)
            if 'v_' in r.text:
                parts = r.text.split('=')[1].split('~')
                price = float(parts[3]) if parts[3] else 0
                prev = float(parts[4]) if parts[4] else price
                pct = (price - prev) / prev * 100 if prev else 0
                return {'price': price, 'pct': pct}
        except: pass
        return {'price': 0, 'pct': 0}
    
    def analyze_stock(self, sym):
        try:
            df = self.ds.load_data(sym)
            if df is None or len(df) < 30:
                return None
            current = df['close'].iloc[-1]
            ma5 = df['close'].rolling(5).mean().iloc[-1]
            ma10 = df['close'].rolling(10).mean().iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1]
            signals = []
            for s in self.strategies:
                try:
                    if s.generate_signal(df) == 1:
                        signals.append(s.name)
                except: pass
            return {'current': current, 'ma5': ma5, 'ma10': ma10, 'ma20': ma20, 
                    'rsi': rsi, 'signals': signals[:5], 'support': ma20 * 0.95,
                    'trend': '多头' if ma5 > ma10 > ma20 else '震荡'}
        except: return None
    
    def generate_report(self, path=None):
        path = path or os.path.expanduser('~/.openclaw/workspace/simulations/portfolio.json')
        with open(path) as f:
            p = json.load(f)
        
        cash = p.get('cash', 0)
        initial = 10000
        positions = p.get('positions', {})
        history = p.get('history', [])
        
        # 计算已实现盈亏 (从卖出记录)
        realized_pnl = 0
        for trade in history:
            if trade.get('profit'):
                realized_pnl += trade['profit']
        
        total_pnl = realized_pnl  # 总盈亏 = 已实现盈亏 + 未实现盈亏
        for sym, pos in positions.items():
            data = self.get_price(sym)
            pos['current_price'] = data['price']
            pos['pct'] = data['pct']
            pnl = (data['price'] - pos['avg_price']) * pos['shares']
            pos['pnl'] = pnl
            total_pnl += pnl  # 加上未实现盈亏
            data = self.get_price(sym)
            pos['current_price'] = data['price']
            pos['pct'] = data['pct']
            pnl = (data['price'] - pos['avg_price']) * pos['shares']
            pos['pnl'] = pnl
            total_pnl += pnl
            pos['analysis'] = self.analyze_stock(sym)
        
        total_value = cash + sum(p.get('current_price',0) * p.get('shares',0) for p in positions.values())
        pnl_pct = total_pnl / initial * 100
        
        # 生成报告
        lines = [f"""
📊 **每日交易报告** - {datetime.now().strftime('%Y-%m-%d %H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏠 **账户概况**
• 本金: ¥{initial:,.2f}
• 现金: ¥{cash:,.2f}
• 持仓: {len(positions)}只

💰 **收益情况**
• 总盈亏: **¥{total_pnl:+,.0f}** ({pnl_pct:+.1f}%)
• 总资产: ¥{total_value:,.2f}
• 现金比例: {cash/total_value*100:.1f}%"""]
        
        # 今日交易
        today = datetime.now().strftime('%Y-%m-%d')
        today_trades = [h for h in history if h.get('date', '').startswith(today)]
        
        lines.append(f"""
📋 **今日交易**""")
        if today_trades:
            for t in today_trades:
                emoji = "🟢" if t.get('type') == 'BUY' else "🔴"
                lines.append(f"   {emoji} {t.get('type')} {t.get('symbol')} @ ¥{t.get('price')} x {t.get('shares')}")
        else:
            lines.append("   ⏸️ 无交易")
        
        # 全部交易历史
        lines.append(f"""
📜 **交易历史 (最近10笔)**""")
        recent = history[-10:] if len(history) > 10 else history
        for t in recent:
            emoji = "🟢" if t.get('type') == 'BUY' else "🔴"
            date = t.get('date', '')[:16]
            lines.append(f"   {emoji} {date} | {t.get('type')} | {t.get('symbol')} @ ¥{t.get('price')}")
        
        # 持仓详情
        lines.append(f"""
📈 **持仓详情**""")
        
        position_list = sorted(positions.items(), key=lambda x: x[1].get('pnl',0), reverse=True)
        
        for i, (sym, pos) in enumerate(position_list, 1):
            curr = pos.get('current_price', 0)
            avg = pos.get('avg_price', 0)
            pnl = pos.get('pnl', 0)
            pct = pos.get('pct', 0)
            analysis = pos.get('analysis')
            
            emoji = "🟢" if pnl >= 0 else "🔴"
            
            lines.append(f"""
{'='*50}
{emoji} {i}. {sym} | {pos.get('name', '未知')[:8]}
{'='*50}
   💵 现价: ¥{curr:.2f} | 成本: ¥{avg:.2f}
   📊 盈亏: ¥{pnl:+,.0f} ({pct:+.2f}%)""")
            
            if analysis:
                a = analysis
                lines.append(f"""
   📉 MA5:¥{a.get('ma5',0):.2f} MA10:¥{a.get('ma10',0):.2f} MA20:¥{a.get('ma20',0):.2f}
   📊 RSI: {a.get('rsi',0):.1f} | 趋势: {a.get('trend', '未知')}
   🎯 策略: {', '.join(a.get('signals', [])) or '无'}""")
            
            # 状态
            pct_pos = (curr - avg) / avg * 100 if avg else 0
            if pct_pos <= -5:
                status = "⚠️ 触及止损"
            elif pct_pos >= 15:
                status = "🎯 触及止盈15%"
            elif pct_pos >= 8:
                status = "⏸️ 触及止盈8%"
            elif pct_pos > 0:
                status = "✅ 盈利持有"
            else:
                status = "📌 正常运行"
            
            lines.append(f"""
   💡 状态: {status} | 买入: {pos.get('buy_date', '未知')}""")
        
        # 操作建议
        lines.append(f"""
{'='*50}
📋 **操作建议**""")
        
        for sym, pos in position_list:
            curr = pos.get('current_price', 0)
            avg = pos.get('avg_price', 1)
            pct_pos = (curr - avg) / avg * 100
            
            if pct_pos <= -5:
                lines.append(f"   🔴 {sym}: 触及止损-5%，建议卖出")
            elif pct_pos >= 15:
                lines.append(f"   🎯 {sym}: 触及止盈+15%，建议卖出")
            elif pct_pos >= 8:
                lines.append(f"   ⏸️ {sym}: 触及止盈+8%，可卖出一半")
            else:
                lines.append(f"   ✅ {sym}: 继续持有")
        
        lines.append("")
        return '\n'.join(lines)


if __name__ == '__main__':
    print(TradingReport().generate_report())
