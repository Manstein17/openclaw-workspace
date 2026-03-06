#!/usr/bin/env python3
"""
Discord 更新日志推送模块
自动将系统更新推送到 Discord 线程

用法:
    python3 discord_changelog.py "新增功能" "描述内容"
    python3 discord_changelog.py "修复" "修复了XX问题"
    python3 discord_changelog.py "参数调整" "XX参数从Y改为Z"
"""

import os
import sys
from datetime import datetime

THREAD_ID = "1476988105260273735"  # 📝 系统更新日志

def post_to_discord(message: str) -> bool:
    """推送消息到 Discord 线程"""
    import subprocess
    
    msg = f"📝 **{datetime.now().strftime('%Y-%m-%d %H:%M')}**\n\n{message}"
    
    cmd = [
        "openclaw", "message", "send",
        "--channel", "discord",
        "--target", THREAD_ID,
        "--message", msg
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"Error posting to Discord: {e}")
        return False

def update_changelog(category: str, content: str) -> bool:
    """追加到 CHANGELOG.md"""
    changelog_path = os.path.expanduser("~/.openclaw/workspace/CHANGELOG.md")
    
    if not os.path.exists(changelog_path):
        print(f"CHANGELOG.md not found at {changelog_path}")
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"- {content}\n"
    
    with open(changelog_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 找到今天的日期块，在对应类别下插入
    # 格式: ## 2026-02-28 后找 ### category
    new_lines = []
    in_today = False
    in_category = False
    inserted = False
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # 检查是否进入今天的日期块
        if line.strip() == f"## {today}":
            in_today = True
            continue
            
        # 如果在今天块内，找到对应类别
        if in_today and not inserted:
            if line.strip().startswith("### ") and not line.strip().startswith(f"### {category}"):
                # 进入下一个类别，说明前面的类别已经结束
                if in_category:
                    inserted = True
                    continue
            
            if f"### {category}" in line:
                in_category = True
                continue
                
            # 在类别下找到列表项位置插入
            if in_category and line.strip().startswith("- "):
                new_lines.append(f"  {content}\n")
                inserted = True
                continue
    
    # 如果没插入成功，追加到末尾
    if not inserted:
        new_lines.append(entry)
    
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    
    return True

def log(category: str, content: str, notify: bool = True):
    """记录并推送更新"""
    # 更新本地 CHANGELOG
    update_changelog(category, content)
    
    # 推送到 Discord
    if notify:
        post_to_discord(f"**{category}**: {content}")
    
    print(f"✅ Logged: {category} - {content}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 2:
        category = sys.argv[1]
        content = " ".join(sys.argv[2:])
        log(category, content)
    else:
        print("用法: python3 discord_changelog.py <分类> <内容>")
        print("分类: 新增功能, 修复, 参数调整, 策略更新")
        print("示例: python3 discord_changelog.py '新增功能' '添加了资金流向检查'")
