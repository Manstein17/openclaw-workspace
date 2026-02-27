#!/usr/bin/env python3
"""
政策记忆模块
长期跟踪政策变化，分析政策趋势
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

POLICY_DIR = "/Users/manstein17/.openclaw/workspace/policy_memory"

class PolicyMemory:
    """政策记忆系统"""
    
    def __init__(self):
        os.makedirs(POLICY_DIR, exist_ok=True)
        self.today = datetime.now().strftime("%Y-%m-%d")
    
    def save_policy(self, policy_name: str, sentiment: str, 
                   key_points: List[str], sectors: List[str],
                   ai_analysis: str = ""):
        """
        保存政策记忆
        """
        policy_file = f"{POLICY_DIR}/{self.today}.json"
        
        # 读取已有政策
        all_policies = self.load_all_policies()
        
        # 更新或添加新政策
        all_policies[policy_name] = {
            "date": self.today,
            "sentiment": sentiment,  # 利好/利空/中性
            "key_points": key_points,
            "sectors": sectors,
            "ai_analysis": ai_analysis,
            "history": all_policies.get(policy_name, {}).get("history", []) + [{
                "date": self.today,
                "sentiment": sentiment,
                "analysis": ai_analysis
            }]
        }
        
        # 保存
        with open(policy_file, 'w', encoding='utf-8') as f:
            json.dump(all_policies, f, ensure_ascii=False, indent=2)
        
        return policy_file
    
    def load_all_policies(self) -> Dict:
        """加载所有政策"""
        policies = {}
        for f in os.listdir(POLICY_DIR):
            if f.endswith('.json'):
                with open(f"{POLICY_DIR}/{f}", 'r', encoding='utf-8') as file:
                    try:
                        data = json.load(file)
                        policies.update(data)
                    except:
                        pass
        return policies
    
    def get_policy_history(self, policy_name: str, days: int = 30) -> List[Dict]:
        """获取政策历史"""
        all_policies = self.load_all_policies()
        policy = all_policies.get(policy_name, {})
        
        history = policy.get("history", [])
        
        # 过滤时间
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        return [h for h in history if h.get("date", "") >= cutoff]
    
    def get_policy_trend(self, policy_name: str) -> str:
        """判断政策趋势"""
        history = self.get_policy_history(policy_name, days=90)
        
        if len(history) < 2:
            return "新政策"
        
        sentiments = [h.get("sentiment", "中性") for h in history]
        
        # 统计情感变化
        bullish_count = sum(1 for s in sentiments if "利好" in s)
        bearish_count = sum(1 for s in sentiments if "利空" in s)
        
        if bullish_count > bearish_count * 2:
            return "持续利好"
        elif bearish_count > bullish_count * 2:
            return "持续利空"
        elif bullish_count > bearish_count:
            return "利好增加"
        elif bearish_count > bullish_count:
            return "利空增加"
        else:
            return "中性稳定"
    
    def get_sector_sentiment(self, sector: str, days: int = 30) -> Dict:
        """获取行业政策情绪"""
        all_policies = self.load_all_policies()
        
        sentiments = []
        for policy_name, data in all_policies.items():
            if sector in data.get("sectors", []):
                sentiment = data.get("sentiment", "中性")
                date = data.get("date", "")
                
                if date >= (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"):
                    sentiments.append({
                        "date": date,
                        "policy": policy_name,
                        "sentiment": sentiment
                    })
        
        # 汇总
        bullish = sum(1 for s in sentiments if "利好" in s.get("sentiment", ""))
        bearish = sum(1 for s in sentiments if "利空" in s.get("sentiment", ""))
        
        if bullish > bearish:
            overall = "利好"
        elif bearish > bullish:
            overall = "利空"
        else:
            overall = "中性"
        
        return {
            "sector": sector,
            "overall": overall,
            "bullish": bullish,
            "bearish": bearish,
            "recent_policies": sentiments
        }
    
    def compare_with_previous(self, policy_name: str) -> str:
        """与上次政策对比"""
        history = self.get_policy_history(policy_name, days=180)
        
        if len(history) < 2:
            return "数据不足，无法比较"
        
        latest = history[-1]
        previous = history[-2]
        
        latest_sentiment = latest.get("sentiment", "中性")
        previous_sentiment = previous.get("sentiment", "中性")
        
        if latest_sentiment == previous_sentiment:
            return f"政策稳定 ({latest_sentiment})"
        elif "利好" in latest_sentiment and "利空" in previous_sentiment:
            return "政策转向利好"
        elif "利空" in latest_sentiment and "利好" in previous_sentiment:
            return "政策转向利空"
        else:
            return f"变化: {previous_sentiment} → {latest_sentiment}"
    
    def generate_policy_report(self) -> str:
        """生成政策报告"""
        all_policies = self.load_all_policies()
        
        report = f"""
=====================================
📜 政策环境报告 ({self.today})
=====================================

"""
        
        # 各行业政策汇总
        sectors = defaultdict(list)
        for policy_name, data in all_policies.items():
            for sector in data.get("sectors", []):
                sectors[sector].append({
                    "policy": policy_name,
                    "sentiment": data.get("sentiment", "中性"),
                    "date": data.get("date", "")
                })
        
        report += "📊 行业政策情绪\n"
        for sector, infos in sorted(sectors.items()):
            bullish = sum(1 for i in infos if "利好" in i["sentiment"])
            bearish = sum(1 for i in infos if "利空" in i["sentiment"])
            
            if bullish > bearish:
                emoji = "🟢"
                status = "利好"
            elif bearish > bullish:
                emoji = "🔴"
                status = "利空"
            else:
                emoji = "🟡"
                status = "中性"
            
            report += f"- {sector}: {emoji} {status} ({bullish}利好/{bearish}利空)\n"
        
        # 政策趋势
        report += "\n📈 政策趋势\n"
        for policy_name in all_policies.keys():
            trend = self.get_policy_trend(policy_name)
            report += f"- {policy_name}: {trend}\n"
        
        return report
    
    def get_investment_recommendation(self, sector: str) -> Dict:
        """获取投资建议（基于政策）"""
        sentiment = self.get_sector_sentiment(sector, days=90)
        trend = self.get_policy_trend(f"{sector}政策")
        
        # 评分
        score = 50  # 基准分
        
        # 根据情绪调整
        if sentiment["overall"] == "利好":
            score += 20
        elif sentiment["overall"] == "利空":
            score -= 20
        
        # 根据趋势调整
        if "利好" in trend:
            score += 10
        elif "利空" in trend:
            score -= 10
        
        # 建议
        if score >= 70:
            recommendation = "强烈推荐"
        elif score >= 55:
            recommendation = "适度推荐"
        elif score >= 45:
            recommendation = "中性"
        elif score >= 30:
            recommendation = "建议回避"
        else:
            recommendation = "强烈回避"
        
        return {
            "sector": sector,
            "score": score,
            "recommendation": recommendation,
            "sentiment": sentiment["overall"],
            "trend": trend
        }


# 测试
if __name__ == "__main__":
    pm = PolicyMemory()
    
    # 测试保存政策
    pm.save_policy(
        "新能源车补贴",
        "利好",
        ["延续补贴", "提高上限"],
        ["新能源", "新能源车"],
        "政策持续利好新能源汽车行业"
    )
    
    # 测试报告
    print(pm.generate_policy_report())
    
    # 测试建议
    rec = pm.get_investment_recommendation("新能源")
    print(f"\n新能源投资建议: {rec}")
