#!/bin/bash
set -e
echo "🚀 部署 OpenClaw..."
git clone git@github.com:Manstein17/--botbot.git botbot-setup
cd botbot-setup
if ! command -v openclaw &> /dev/null; then npm install -g openclaw; fi
cp openclaw-config.json ~/.openclaw/openclaw.json
mkdir -p ~/.openclaw/workspace
cp -r workspace/* ~/.openclaw/workspace/
openclaw gateway restart
echo "✅ 部署完成！"
