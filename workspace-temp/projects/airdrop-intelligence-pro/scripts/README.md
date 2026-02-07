# Airdrop Monitor Scripts

This directory contains scripts for automated airdrop monitoring and discovery.

## Scripts Overview

### 1. `search-airdrops.js`
Searches the web for airdrop opportunities using Brave Search API.

**Features:**
- Searches multiple query variations
- Calculates relevance scores
- Filters out scams and spam
- Saves results to database

**Usage:**
```bash
node scripts/search-airdrops.js
```

### 2. `discord-airdrop-monitor.js`
Monitors Discord channels for airdrop announcements.

**Features:**
- Monitors popular crypto project Discord servers
- Detects airdrop keywords in messages
- Extracts project names and links
- Saves to database

**Usage:**
```bash
node scripts/discord-airdrop-monitor.js
```

**Configuration (in .env):**
```
DISCORD_BOT_TOKEN=your-bot-token
```

### 3. `run-airdrop-monitor.sh`
Main execution script that runs all monitoring tasks.

**Features:**
- Runs web search
- Checks Discord channels
- Generates summary report
- Handles logging

**Usage:**
```bash
bash scripts/run-airdrop-monitor.sh
```

**Commands:**
- `bash scripts/run-airdrop-monitor.sh` - Run full monitoring
- `bash scripts/run-airdrop-monitor.sh web` - Web search only
- `bash scripts/run-airdrop-monitor.sh discord` - Discord check only
- `bash scripts/run-airdrop-monitor.sh report` - Database summary

### 4. `setup-cron.sh`
Configures automatic scheduling.

**Usage:**
```bash
bash scripts/setup-cron.sh
```

## Configuration

### Environment Variables (.env)

```env
# Discord Bot (for monitoring)
DISCORD_BOT_TOKEN=your-bot-token

# Brave Search API (for web search)
BRAVE_API_KEY=your-api-key

# Optional: Notification channels
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id
DISCORD_WEBHOOK_URL=your-webhook-url
```

## Database Schema

The scripts use Prisma with SQLite. The main model is `Airdrop`:

| Field | Type | Description |
|-------|------|-------------|
| id | String | Unique identifier |
| name | String | Project name |
| slug | String | URL-friendly slug |
| description | String | Project description |
| category | String | DeFi, NFT, GameFi, etc. |
| status | String | upcoming, active, ended |
| difficulty | String | easy, medium, hard |
| source | String | web_search, discord |
| website | String | Project URL |
| discord | String | Discord URL |
| twitter | String | Twitter URL |

## Log Files

Logs are written to: `~/.openclaw/logs/airdrop-monitor.log`

## Cron Schedule

The monitoring runs every 30 minutes automatically.

**Manual control:**
```bash
# View cron jobs
openclaw cron list

# Run immediately
openclaw cron run <job-id>

# Disable
openclaw cron disable <job-id>

# Enable
openclaw cron enable <job-id>
```

## Keywords Monitored

### Airdrop Keywords
- airdrop, token, claim, free token
- giveaway, testnet, snapshot
- eligibility, whitelist
- 分配, 空投, 代币 (Chinese)

### Monitored Servers
- LayerZero, Arbitrum, Optimism
- ZkSync, StarkNet, Metamask
- Uniswap, Blur, Magic Eden
- Yuga Labs and more...

## Troubleshooting

### "DISCORD_BOT_TOKEN not found"
Add your Discord bot token to the `.env` file.

### "BRAVE_API_KEY not found"
Web search will be skipped. Add your Brave API key to enable.

### No new airdrops found
- Check your internet connection
- Verify API keys are valid
- Check log file for errors
- Try running manually: `bash scripts/run-airdrop-monitor.sh`
