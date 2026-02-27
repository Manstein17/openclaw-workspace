#!/usr/bin/env python3
"""
政策分析模块 V2
- 官方来源优先（证监会、央行、财政部等）
- 过滤KOL言论
- 每天抓取1-2次
"""
import akshare as ak
import requests
from datetime import datetime
import json
import os

POLICY_CACHE = "/tmp/policy_news.json"

# 官方来源列表
OFFICIAL_SOURCES = [
    '新华社',
    '人民日报', 
    '央视',
    '证监会',
    '央行',
    '财政部',
    '工信部',
    '发改委',
    '商务部',
    '国资委',
    '证监会官网',
    '中国政府网',
    '新华财经',
]

# 需要过滤的KOL/自媒体的关键词
FILTER_KEYWORDS = [
    '大V', '大v', '专家称', '业内人士', '散户', '公募', '私募',
    '基金经理', '分析师', '股评', '名家', '专栏', '微博',
    '知乎', '雪球', '东财', '同花顺', '社区', '用户',
]

# 只抓取的官方政策关键词（更宽松）
POLICY_KEYWORDS = [
    # 监管机构
    '证监会', '央行', '财政部', '工信部', '发改委', '商务部', '国资委',
    '银保监会', '金融监管', '交易所', '证监会',
    # 政策文件
    '政策', '通知', '公告', '意见', '办法', '规定', '条例',
    # 具体政策
    'IPO', '注册制', '退市', '减持', '回购', '分红',
    '降准', '降息', '加息', 'LPR', 'MLF',
    '补贴', '税收', '优惠', '支持', '禁止', '打击',
    # 行业
    '新能源', '光伏', '风电', '储能', '新能源车', '电动车',
    '芯片', '半导体', '人工智能', 'AI', '房地产', '银行',
    '保险', '医药', '白酒', '茅台',
    # 市场
    'A股', '股市', '大盘', '指数', '涨停', '跌停',
    '资金', '北向', '外资', '基金', '机构',
]


class AutoPolicyFetcher:
    """政策抓取 - 官方来源优先"""
    
    def __init__(self):
        self.cache = self._load_cache()
        self.last_fetch = self.cache.get('last_fetch', '')
    
    def _load_cache(self):
        if os.path.exists(POLICY_CACHE):
            try:
                with open(POLICY_CACHE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'news': [], 'last_update': '', 'last_fetch': ''}
    
    def _save_cache(self):
        with open(POLICY_CACHE, 'w') as f:
            json.dump(self.cache, f, ensure_ascii=False)
    
    def should_fetch(self) -> bool:
        """判断是否需要抓取（每天1-2次）"""
        last = self.cache.get('last_fetch', '')
        if not last:
            return True
        
        try:
            last_dt = datetime.strptime(last, '%Y-%m-%d %H:%M')
            # 超过12小时抓取一次
            if (datetime.now() - last_dt).total_seconds() > 12 * 3600:
                return True
        except:
            return True
        
        return False
    
    def fetch_policy_news(self) -> list:
        """抓取官方政策新闻"""
        
        # 检查是否需要抓取
        if not self.should_fetch() and self.cache.get('news'):
            print(f"   使用缓存新闻 (上次: {self.cache.get('last_fetch')})")
            return self.cache.get('news', [])
        
        print("   正在抓取官方政策...")
        news_list = []
        
        # 1. 尝试从官方来源抓取
        try:
            # 财经网站新闻
            df = ak.stock_news_em(symbol="全球")
            if df is not None and len(df) > 0:
                for _, row in df.head(50).iterrows():
                    title = str(row.get('新闻标题', ''))
                    source = str(row.get('文章来源', ''))
                    date = str(row.get('发布时间', ''))
                    
                    # 过滤KOL
                    if self._is_kol_content(title, source):
                        continue
                    
                    # 只保留政策相关
                    if self._is_policy_related(title):
                        news_list.append({
                            'title': title,
                            'date': date,
                            'source': source,
                            'is_official': self._is_official_source(source)
                        })
        except Exception as e:
            print(f"   抓取错误: {e}")
        
        # 2. 去重和排序
        seen = set()
        unique_news = []
        for n in news_list:
            title = n['title']
            if title not in seen and len(title) > 5:
                seen.add(title)
                unique_news.append(n)
        
        # 按官方优先排序
        unique_news.sort(key=lambda x: (x.get('is_official', False), -len(x['title'])), reverse=True)
        
        # 保存
        self.cache['news'] = unique_news[:15]  # 最多15条
        self.cache['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.cache['last_fetch'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        self._save_cache()
        
        print(f"   抓取完成: {len(unique_news)}条 (官方{sum(1 for n in unique_news if n.get('is_official'))}条)")
        
        return unique_news[:15]
    
    def _is_official_source(self, source: str) -> bool:
        """判断是否官方来源"""
        for official in OFFICIAL_SOURCES:
            if official in source:
                return True
        return False
    
    def _is_kol_content(self, title: str, source: str) -> bool:
        """过滤KOL/自媒体内容"""
        # 检查来源
        for filter_kw in FILTER_KEYWORDS:
            if filter_kw in source:
                return True
        
        # 过滤标题中带有明显观点性的
        opinion_phrases = ['认为', '预测', '建议', '称', '指出', '坦言', '直言']
        count = sum(1 for p in opinion_phrases if p in title)
        if count >= 2:  # 多个观点词，很可能是KOL
            return True
        
        return False
    
    def _is_policy_related(self, title: str) -> bool:
        """判断是否相关（宽松模式 - 只要是财经新闻就保留）"""
        # 基本上所有新闻都保留，过滤在后面处理
        return True
    
    def analyze_policy(self, news_list: list) -> dict:
        """分析政策影响"""
        sectors = {
            '新能源': [],
            '新能源车': [],
            '医药': [],
            '芯片': [],
            '白酒': [],
            '银行': [],
            '保险': [],
            '房地产': [],
            '互联网': [],
        }
        
        sector_keywords = {
            '新能源': ['新能源', '光伏', '风电', '储能', '绿电', '电力'],
            '新能源车': ['新能源车', '电动车', '锂电池', '比亚迪', '宁德', '汽车'],
            '医药': ['医药', '医保', '中药', '医疗器械', '创新药'],
            '芯片': ['芯片', '半导体', '集成电路', 'AI', '算力', '芯片'],
            '白酒': ['白酒', '茅台', '五粮液', '酒', '消费'],
            '银行': ['银行', '金融', '信贷', '存款'],
            '保险': ['保险', '险资', '养老金'],
            '房地产': ['房地产', '地产', '房贷', '限购', '楼'],
            '互联网': ['互联网', '平台', '电商', '数字经济'],
        }
        
        for news in news_list:
            title = news.get('title', '')
            
            for sector, keywords in sector_keywords.items():
                if any(k in title for k in keywords):
                    # 判断是利好还是利空
                    positive = ['利好', '支持', '补贴', '优惠', '鼓励', '促进', '加大', '提高']
                    negative = ['利空', '打击', '限制', '禁止', '严控', '收紧', '从严', '暂停']
                    
                    if any(p in title for p in positive):
                        sentiment = '利好'
                    elif any(n in title for n in negative):
                        sentiment = '利空'
                    else:
                        sentiment = '中性'
                    
                    sectors[sector].append({
                        'title': title[:60],
                        'sentiment': sentiment,
                        'is_official': news.get('is_official', False)
                    })
        
        return sectors
    
    def get_policy_summary(self) -> str:
        """获取政策摘要"""
        news = self.fetch_policy_news()
        
        # 分析影响
        sector_impact = self.analyze_policy(news)
        
        summary = "【政策要点】\n"
        
        official_count = sum(1 for n in news if n.get('is_official'))
        summary += f"官方来源: {official_count}条 | 总计: {len(news)}条\n\n"
        
        for sector, infos in sector_impact.items():
            if infos:
                bullish = sum(1 for i in infos if i['sentiment'] == '利好')
                bearish = sum(1 for i in infos if i['sentiment'] == '利空')
                official = sum(1 for i in infos if i.get('is_official'))
                
                if bullish > bearish:
                    emoji = "🟢"
                    status = f"利好({bullish}条)"
                elif bearish > bullish:
                    emoji = "🔴"
                    status = f"利空({bearish}条)"
                else:
                    emoji = "🟡"
                    status = "中性"
                
                official_tag = "📢" if official > 0 else ""
                summary += f"- {sector}: {emoji} {status} {official_tag}\n"
        
        return summary if summary != "【政策要点】\n" else "【政策要点】\n今日无重大政策"


# 测试
if __name__ == "__main__":
    fetcher = AutoPolicyFetcher()
    print(fetcher.get_policy_summary())
