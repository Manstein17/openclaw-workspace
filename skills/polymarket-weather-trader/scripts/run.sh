#!/bin/bash
# Weather Trader wrapper - sets API key before running

export SIMMER_API_KEY="sk_live_XXXXX_REDACTED"

cd ~/.openclaw/workspace/skills/polymarket-weather-trader
python3 weather_trader.py "$@"
