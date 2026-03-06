#!/bin/bash
# Wrapper script to run Elon Tweet Trader with API key
export SIMMER_API_KEY="sk_live_REDACTED"
cd ~/.openclaw/workspace/skills/polymarket-elon-tweets
python3 elon_tweets.py "$@"
