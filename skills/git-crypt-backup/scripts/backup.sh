#!/bin/bash
# Git-crypt backup script for OpenClaw

set -e

TIMESTAMP=$(date +"%Y-%m-%d %H%M")

backup_repo() {
    local path=$1
    local name=$2
    
    if [[ ! -d "$path" ]]; then
        echo "⏭️  $name: directory not found, skipping"
        return
    fi
    
    cd "$path"
    
    # Check if it's a git repo
    if [[ ! -d .git ]]; then
        echo "⏭️  $name: not a git repo, skipping"
        return
    fi
    
    # Check if there are changes
    if [[ -n $(git status --porcelain) ]]; then
        git add -A
        git commit -m "Auto backup: $TIMESTAMP"
        git push
        echo "✅ $name: backed up"
    else
        echo "⏭️  $name: no changes"
    fi
}

echo "🔄 Starting git-crypt backup..."

# Backup workspace
backup_repo "$HOME/.openclaw/workspace" "workspace"

# Backup config (using our custom backup dir)
backup_repo "$HOME/.openclaw-backup-config" "config"

echo "✅ Backup complete!"
