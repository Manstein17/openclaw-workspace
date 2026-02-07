#!/bin/bash

# ==========================================
# Airdrop Monitor Cron Setup Script
# Configures automatic airdrop monitoring
# ==========================================

# Configuration
PROJECT_DIR="/Users/manstein17/.openclaw/workspace/projects/airdrop-intelligence-pro"
SCRIPT_PATH="$PROJECT_DIR/scripts/run-airdrop-monitor.sh"
LOG_FILE="$HOME/.openclaw/logs/airdrop-monitor.log"
CRON_EXPRESSION="*/30 * * * *"  # Every 30 minutes

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           🪂 AIRDROP MONITOR CRON SETUP 🪂                   ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "${RED}❌ Error: Script not found at $SCRIPT_PATH${NC}"
    exit 1
fi

# Ensure log directory exists
if [ ! -d "$(dirname $LOG_FILE)" ]; then
    mkdir -p "$(dirname $LOG_FILE)"
    echo -e "${GREEN}✓ Created log directory: $(dirname $LOG_FILE)${NC}"
fi

# Ensure script is executable
chmod +x "$SCRIPT_PATH"
echo -e "${GREEN}✓ Made script executable: $SCRIPT_PATH${NC}"

# Generate cron job command
CRON_CMD="cd $PROJECT_DIR && bash $SCRIPT_PATH >> $LOG_FILE 2>&1"

echo ""
echo "Cron Configuration:"
echo "  Expression: $CRON_EXPRESSION (every 30 minutes)"
echo "  Log file: $LOG_FILE"
echo ""

# Check if openclaw is available
if command -v openclaw &> /dev/null; then
    echo -e "${GREEN}Using OpenClaw cron system...${NC}"
    
    # Add cron job using openclaw
    openclaw cron add \
        --name "airdrop-monitor" \
        --schedule "*/30 * * * *" \
        --command "bash $SCRIPT_PATH" \
        --log "$LOG_FILE" \
        --description "Search for new crypto airdrops every 30 minutes"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Cron job added successfully via OpenClaw${NC}"
    else
        echo -e "${RED}✗ Failed to add cron job via OpenClaw${NC}"
        echo ""
        echo "Falling back to manual crontab entry..."
        
        # Add to crontab as fallback
        (crontab -l 2>/dev/null | grep -v "airdrop-monitor"; echo "# Airdrop Monitor - Every 30 minutes"; echo "$CRON_EXPRESSION $CRON_CMD # airdrop-monitor") | crontab -
        echo -e "${GREEN}✓ Added to crontab${NC}"
    fi
else
    echo -e "${YELLOW}OpenClaw not found, using system crontab...${NC}"
    
    # Add to crontab
    (crontab -l 2>/dev/null | grep -v "airdrop-monitor"; echo "# Airdrop Monitor - Every 30 minutes"; echo "$CRON_EXPRESSION $CRON_CMD # airdrop-monitor") | crontab -
    echo -e "${GREEN}✓ Added to crontab${NC}"
fi

echo ""
echo "Current crontab entries:"
crontab -l 2>/dev/null | grep -A2 "airdrop\|# Airdrop" || echo "  (no airdrop-related entries)"

echo ""
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo ""
echo "Manual Commands:"
echo "  Run now:       bash $SCRIPT_PATH"
echo "  View logs:     tail -f $LOG_FILE"
echo "  Test search:   node $PROJECT_DIR/scripts/search-airdrops.js"
echo ""
