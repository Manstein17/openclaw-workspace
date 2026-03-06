#!/bin/bash
# 开发助手 - 用法: dev "任务描述"
# 示例: dev "优化日志输出"

cd ~/.openclaw/workspace

# 读取需求文档
REQUIREMENTS=$(cat REQUIREMENTS.md 2>/dev/null || echo "无需求文档")

# 构造任务
TASK="$1

项目位置: ~/.openclaw/workspace

需求文档:
$REQUIREMENTS

请直接修改代码文件，完成后汇报改动内容。"

# 启动ACPP会话
openclaw acp client --session "dev" --no-prefix-cwd << EOF
$TASK
EOF
