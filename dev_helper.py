#!/usr/bin/env python3
"""
开发助手 - 调用ACXP协助开发交易系统
用法: python dev_helper.py "开发任务描述"
"""
import sys
import os
import subprocess

# 项目根目录
PROJECT_DIR = os.path.expanduser("~/.openclaw/workspace")
os.chdir(PROJECT_DIR)

def main():
    if len(sys.argv) < 2:
        print("用法: python dev_helper.py \"开发任务描述\"")
        print("示例: python dev_helper.py \"优化realtime_trader.py的日志输出\"")
        sys.exit(1)
    
    task = sys.argv[1]
    
    print(f"🎯 任务: {task}")
    print("=" * 50)
    
    # 读取需求文档
    req_file = os.path.join(PROJECT_DIR, "REQUIREMENTS.md")
    if os.path.exists(req_file):
        with open(req_file) as f:
            requirements = f.read()
    else:
        requirements = "无需求文档"
    
    # 构造完整任务
    full_task = f"""
开发交易系统任务: {task}

项目位置: {PROJECT_DIR}

需求文档:
{requirements}

请直接修改相关文件，完成后说明做了哪些改动。
"""
    
    # 调用ACP
    cmd = [
        "openclaw", "acp", "client",
        "--session", "dev",
        "--no-prefix-cwd"
    ]
    
    print(f"\n🚀 启动ACXP...\n")
    
    # 启动交互式会话
    subprocess.run(cmd)

if __name__ == "__main__":
    main()
