#!/bin/bash
# Daily backup script for OpenClaw

set -e

TIMESTAMP=$(date +"%Y-%m-%d %H%M")

echo "🔄 Starting OpenClaw backup..."

BACKUP_DIR="$HOME/openclaw-backups"
mkdir -p "$BACKUP_DIR"

# Backup OpenClaw directory
BACKUP_FILE="$BACKUP_DIR/openclaw-$TIMESTAMP.tar.gz"

# Exclude large/regeneratable files
tar -czf "$BACKUP_FILE" \
    --exclude='*.log' \
    --exclude='completions' \
    --exclude='media/inbound' \
    --exclude='media/outbound' \
    --exclude='.git' \
    "$HOME/.openclaw" 2>/dev/null || true

echo "✅ Backed up to: $BACKUP_FILE"

# Keep only last 7 backups
cd "$BACKUP_DIR"
ls -t openclaw-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "✅ Backup complete! ($(ls -1 openclaw-*.tar.gz 2>/dev/null | wc -l) backups kept)"
