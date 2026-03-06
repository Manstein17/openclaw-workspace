#!/usr/bin/env python3
"""
政策新闻独立抓取
每3小时自动抓取，调用LLM分析
"""
import time
import sys
import os
sys.path.insert(0, '/Users/manstein17/.openclaw/workspace')

from auto_policy import AutoPolicyFetcher
from llm_analyzer import LLMStockAnalyzer

def run():
    print("=" * 50)
    print("📰 政策新闻自动抓取")
    print("⏰ 间隔: 每3小时")
    print("=" * 50)
    
    policy = AutoPolicyFetcher()
    
    while True:
        print(f"\n🕐 {time.strftime('%Y-%m-%d %H:%M')} 开始抓取政策新闻...")
        
        try:
            news = policy.fetch_policy_news()
            print(f"✅ 抓取完成: {len(news)}条")
            
            # 规则分析
            sectors = policy.analyze_policy(news)
            print(f"📊 行业分析: {list(sectors.keys())}")
            
            # LLM分析
            print("🤖 调用LLM分析政策...")
            llm = LLMStockAnalyzer()
            # 构建政策摘要
            policy_summary = policy.get_policy_summary()
            if policy_summary:
                llm_result = llm.analyze_policy(policy_summary)
                if llm_result.get('success'):
                    print(f"📝 LLM分析:\n{llm_result.get('analysis', '')[:300]}...")
                else:
                    print(f"⚠️ LLM分析失败: {llm_result.get('error')}")
            
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
        
        # 每3小时抓取一次
        print("⏳ 下次抓取: 3小时后...")
        time.sleep(3 * 3600)

if __name__ == '__main__':
    run()
