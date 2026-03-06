#!/usr/bin/env python3
"""
自动更新日志到Discord
每次新增功能或修复问题时自动发送通知
"""
import os
import sys
import json
import subprocess
from datetime import datetime

CHANNEL_ID = "1474091136594350140"  # Discord频道ID
LOG_FILE = "/Users/manstein17/.openclaw/workspace/CHANGELOG.md"

def send_discord(message: str):
    """发送消息到Discord"""
    try:
        # 使用OpenClaw的message工具
        cmd = f'''
curl -s -X POST "https://discord.com/api/v10/channels/{CHANNEL_ID}/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bot $(cat ~/.openclaw/.credentials/discord_bot_token.txt 2>/dev/null)" \
  -d '{{"content": {json.dumps(message[:2000])}}}'
'''
        subprocess.run(cmd, shell=True, capture_output=True)
    except Exception as e:
        print(f"发送失败: {e}")

def check_updates():
    """检查是否有更新"""
    if not os.path.exists(LOG_FILE):
        return
    
    # 读取最新修改时间
    mtime = os.path.getmtime(LOG_FILE)
    now = datetime.now().timestamp()
    
    # 如果5分钟内修改过，发送通知
    if now - mtime < 300:
        with open(LOG_FILE) as f:
            content = f.read()
            lines = content.split('\n')[:20]  # 取前20行
            msg = "📝 **系统更新**\n" + '\n'.join(lines)
            send_discord(msg)

if __name__ == "__main__":
    check_updates()
