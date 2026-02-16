#!/bin/bash
# Simple backup script for OpenClaw (no git, just tar)

set -e

TIMESTAMP=$(date +"%Y-%m-%d_%H%M")

echo "🔄 Starting simple backup..."

BACKUP_DIR="$HOME/openclaw-backups"
mkdir -p "$BACKUP_DIR"

# Backup file name
BACKUP_FILE="$BACKUP_DIR/openclaw-$TIMESTAMP.tar.gz"

# Create backup (exclude large/regeneratable files)
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

echo "✅ Backup complete! ($(ls -1 openclaw-*.tar.gz 2>/dev/null | wc -l | tr -d ' ') backups kept)"
