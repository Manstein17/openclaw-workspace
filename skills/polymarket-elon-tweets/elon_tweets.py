#!/usr/bin/env python3
"""
Simmer Elon Tweet Trader Skill

Trades Polymarket "Elon Musk # tweets" markets using XTracker post counts.
Inspired by @noovd's $345K strategy: buy adjacent range buckets when their
combined cost is less than $1 (one always resolves YES = $1).

Usage:
    python elon_tweets.py              # Dry run (show opportunities, no trades)
    python elon_tweets.py --live       # Execute real trades
    python elon_tweets.py --positions  # Show current positions only
    python elon_tweets.py --stats      # Show XTracker stats only

Requires:
    pip install simmer-sdk
    SIMMER_API_KEY environment variable (get from simmer.markets/dashboard)
    WALLET_PRIVATE_KEY environment variable (for external wallet trading)
"""

import os
import sys
import re
import json
import argparse
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

# Force line-buffered stdout so output is visible in non-TTY environments (cron, Docker, OpenClaw)
sys.stdout.reconfigure(line_buffering=True)

# Optional: Trade Journal integration for tracking
try:
    from tradejournal import log_trade
    JOURNAL_AVAILABLE = True
except ImportError:
    try:
        from skills.tradejournal import log_trade
        JOURNAL_AVAILABLE = True
    except ImportError:
        JOURNAL_AVAILABLE = False
        def log_trade(*args, **kwargs):
            pass  # No-op if tradejournal not installed

# =============================================================================
# Configuration (config.json > env vars > defaults)
# =============================================================================

def _load_config(schema, skill_file, config_filename="config.json"):
    """Load config with priority: config.json > env vars > defaults."""
    from pathlib import Path
    config_path = Path(skill_file).parent / config_filename
    file_cfg = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                file_cfg = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    result = {}
    for key, spec in schema.items():
        if key in file_cfg:
            result[key] = file_cfg[key]
        elif spec.get("env") and os.environ.get(spec["env"]):
            val = os.environ.get(spec["env"])
            type_fn = spec.get("type", str)
            try:
                result[key] = type_fn(val) if type_fn != str else val
            except (ValueError, TypeError):
                result[key] = spec.get("default")
        else:
            result[key] = spec.get("default")
    return result

def _get_config_path(skill_file, config_filename="config.json"):
    from pathlib import Path
    return Path(skill_file).parent / config_filename

def _update_config(updates, skill_file, config_filename="config.json"):
    from pathlib import Path
    config_path = Path(skill_file).parent / config_filename
    existing = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    existing.update(updates)
    with open(config_path, "w") as f:
        json.dump(existing, f, indent=2)
    return existing

load_config = _load_config
get_config_path = _get_config_path
update_config = _update_config

CONFIG_SCHEMA = {
    "max_bucket_sum": {"env": "SIMMER_ELON_MAX_BUCKET_SUM", "default": 0.90, "type": float},
    "max_position_usd": {"env": "SIMMER_ELON_MAX_POSITION", "default": 5.00, "type": float},
    "bucket_spread": {"env": "SIMMER_ELON_BUCKET_SPREAD", "default": 1, "type": int},
    "sizing_pct": {"env": "SIMMER_ELON_SIZING_PCT", "default": 0.05, "type": float},
    "max_trades_per_run": {"env": "SIMMER_ELON_MAX_TRADES", "default": 6, "type": int},
    "exit_threshold": {"env": "SIMMER_ELON_EXIT", "default": 0.65, "type": float},
    "slippage_max_pct": {"env": "SIMMER_ELON_SLIPPAGE_MAX", "default": 0.05, "type": float},
    "min_position_usd": {"env": "SIMMER_ELON_MIN_POSITION", "default": 2.00, "type": float},
    "data_source": {"env": "SIMMER_ELON_DATA_SOURCE", "default": "xtracker", "type": str},
}

_config = load_config(CONFIG_SCHEMA, __file__)


def _reload_config_globals():
    """Reload module-level config globals from disk (used after --set)."""
    global _config, MAX_BUCKET_SUM, MAX_POSITION_USD, BUCKET_SPREAD, SMART_SIZING_PCT
    global MAX_TRADES_PER_RUN, EXIT_THRESHOLD, SLIPPAGE_MAX_PCT, MIN_POSITION_USD, DATA_SOURCE
    _config = load_config(CONFIG_SCHEMA, __file__)
    MAX_BUCKET_SUM = _config["max_bucket_sum"]
    MAX_POSITION_USD = _config["max_position_usd"]
    BUCKET_SPREAD = _config["bucket_spread"]
    SMART_SIZING_PCT = _config["sizing_pct"]
    MAX_TRADES_PER_RUN = _config["max_trades_per_run"]
    EXIT_THRESHOLD = _config["exit_threshold"]
    SLIPPAGE_MAX_PCT = _config["slippage_max_pct"]
    MIN_POSITION_USD = _config["min_position_usd"]
    DATA_SOURCE = _config["data_source"]


XTRACKER_API_BASE = "https://xtracker.polymarket.com/api"

# Source tag for tracking
TRADE_SOURCE = "sdk:elon-tweets"

# Polymarket constraints
MIN_SHARES_PER_ORDER = 5.0
MIN_TICK_SIZE = 0.01

# Strategy parameters
MAX_BUCKET_SUM = _config["max_bucket_sum"]
MAX_POSITION_USD = _config["max_position_usd"]
BUCKET_SPREAD = _config["bucket_spread"]
SMART_SIZING_PCT = _config["sizing_pct"]
MAX_TRADES_PER_RUN = _config["max_trades_per_run"]
EXIT_THRESHOLD = _config["exit_threshold"]
SLIPPAGE_MAX_PCT = _config["slippage_max_pct"]
MIN_POSITION_USD = _config["min_position_usd"]
DATA_SOURCE = _config["data_source"]

# Context safeguard thresholds
TIME_TO_RESOLUTION_MIN_HOURS = 1  # Tweet markets are shorter, allow closer-to-resolution trades

# =============================================================================
# SDK Client (handles wallet linking, signing, CLOB creds automatically)
# =============================================================================

_client = None

def get_client():
    """Lazy-init SimmerClient singleton."""
    global _client
    if _client is None:
        try:
            from simmer_sdk import SimmerClient
        except ImportError:
            print("Error: simmer-sdk not installed. Run: pip install simmer-sdk")
            sys.exit(1)
        api_key = os.environ.get("SIMMER_API_KEY")
        if not api_key:
            # Try to read from credentials file
            cred_file = os.path.expanduser("~/.openclaw/workspace/.credentials/simmer-api.txt")
            if os.path.exists(cred_file):
                with open(cred_file, "r") as f:
                    api_key = f.read().strip()
        if not api_key:
            print("Error: SIMMER_API_KEY environment variable not set")
            print("Get your API key from: simmer.markets/dashboard → SDK tab")
            sys.exit(1)
        _client = SimmerClient(api_key=api_key, venue="simmer")  # Default to simulation
    return _client

# =============================================================================
# HTTP helper (for XTracker — public API, no auth)
# =============================================================================

def fetch_json(url, headers=None):
    """Fetch JSON from URL with error handling."""
    try:
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        print(f"  HTTP Error {e.code}: {url}")
        return None
    except URLError as e:
        print(f"  URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
        return None


# =============================================================================
# XTracker API
# =============================================================================

def get_xtracker_trackings():
    """Get active tracking periods for Elon Musk from XTracker."""
    url = f"{XTRACKER_API_BASE}/users/elonmusk/trackings?activeOnly=true"
    data = fetch_json(url)
    if not data or not data.get("success"):
        print("  Failed to fetch XTracker trackings")
        return []
    return data.get("data", [])


def get_xtracker_stats(tracking_id):
    """Get stats for a specific tracking period (includes current count + pace projection)."""
    url = f"{XTRACKER_API_BASE}/trackings/{tracking_id}?includeStats=true"
    data = fetch_json(url)
    if not data or not data.get("success"):
        return None
    return data.get("data", {})


# =============================================================================
# Market parsing
# =============================================================================

def parse_tweet_range(text):
    """Parse a tweet count range from market title/outcome. Returns (low, high) or None."""
    if not text:
        return None

    # "0-19" or "200-219" style
    range_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', text)
    if range_match:
        return (int(range_match.group(1)), int(range_match.group(2)))

    # "300 or more" / "300+" style
    above_match = re.search(r'(\d+)\s*(?:or more|\+|or higher|or above)', text, re.IGNORECASE)
    if above_match:
        return (int(above_match.group(1)), 999999)

    # "less than 20" / "under 20" style
    below_match = re.search(r'(?:less than|under|below)\s*(\d+)', text, re.IGNORECASE)
    if below_match:
        return (0, int(below_match.group(1)) - 1)

    return None


def match_tracking_to_event(tracking_title, event_name):
    """Check if an XTracker tracking title matches a Simmer event name."""
    if not tracking_title or not event_name:
        return False
    # Normalize: lowercase, strip "?" marks, collapse whitespace
    t = re.sub(r'\s+', ' ', tracking_title.lower().strip().rstrip('?'))
    e = re.sub(r'\s+', ' ', event_name.lower().strip().rstrip('?'))
    # Check if one contains the other (event names may be truncated)
    return t in e or e in t


# =============================================================================
# Simmer API (via SDK client)
# =============================================================================

def get_portfolio():
    try:
        return get_client().get_portfolio()
    except Exception as e:
        print(f"  ⚠️  Portfolio fetch failed: {e}")
        return None


def get_market_context(market_id, my_probability=None):
    try:
        endpoint = f"/api/sdk/context/{market_id}"
        if my_probability is not None:
            endpoint += f"?my_probability={my_probability}"
        return get_client()._request("GET", endpoint)
    except Exception:
        return None


def get_positions():
    try:
        return get_client().get_positions()
    except Exception as e:
        print(f"  Error fetching positions: {e}")
        return []


def execute_trade(market_id, side, amount):
    """Execute a buy trade with source tagging."""
    try:
        result = get_client().trade(
            market_id=market_id,
            side=side,
            amount=amount,
            source=TRADE_SOURCE,
        )
        return {
            "success": result.success,
            "trade_id": result.trade_id,
            "shares_bought": result.shares_bought,
            "shares": result.shares_bought,
            "error": result.error,
        }
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Local Trade Journal (JSON file)
# =============================================================================

TRADE_LOG_FILE = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_trades.json")

def _ensure_trade_log_dir():
    """Ensure the trade log directory exists."""
    log_dir = os.path.dirname(TRADE_LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

def load_trade_log():
    """Load existing trade log from JSON file."""
    _ensure_trade_log_dir()
    if os.path.exists(TRADE_LOG_FILE):
        try:
            with open(TRADE_LOG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_trade_record(record):
    """Save a trade record to local JSON file."""
    _ensure_trade_log_dir()
    trades = load_trade_log()
    trades.append(record)
    with open(TRADE_LOG_FILE, "w") as f:
        json.dump(trades, f, indent=2)

# =============================================================================
# Enhanced Trade Journal with P&L Tracking
# =============================================================================

SELL_TARGETS = [
    {"price": 0.30, "action": "提示", "reason": "30% - 初步盈利"},
    {"price": 0.50, "action": "考虑卖出", "reason": "50% - 半仓获利"},
    {"price": 0.70, "action": "建议卖出", "reason": "70% - 大幅盈利"},
    {"price": 0.80, "action": "强制卖出", "reason": "80% - 止盈线"},
    {"price": 0.90, "action": "强烈建议卖出", "reason": "90% - 接近目标"},
]

def calculate_position_pnl(position_shares, position_cost, current_price):
    """计算持仓盈亏"""
    if position_shares == 0 or position_cost == 0:
        return {"current_value": 0, "pnl": 0, "pnl_percent": 0}
    current_value = position_shares * current_price
    pnl = current_value - position_cost
    pnl_percent = (pnl / position_cost) * 100 if position_cost > 0 else 0
    return {
        "current_value": current_value,
        "pnl": pnl,
        "pnl_percent": pnl_percent,
    }

def check_sell_signals(bucket, current_price, shares, cost):
    """检查是否触发卖出信号"""
    if current_price == 0 or shares == 0:
        return []
    
    pnl_info = calculate_position_pnl(shares, cost, current_price)
    signals = []
    
    for target in SELL_TARGETS:
        if current_price >= target["price"]:
            signals.append({
                "bucket": bucket,
                "current_price": current_price,
                "target_price": target["price"],
                "action": target["action"],
                "reason": target["reason"],
                "shares": shares,
                "cost": cost,
                "current_value": pnl_info["current_value"],
                "pnl": pnl_info["pnl"],
                "pnl_percent": pnl_info["pnl_percent"],
            })
    
    return signals

def log_trade_record(
    market_id,
    market_question,
    bucket_label,
    price,
    amount,
    shares,
    action="buy",
    dry_run=True,
    trade_id=None,
    error=None,
    projected_count=None,
    current_count=None,
    cluster_cost=None,
    pnl=None,
    sell_reason=None,
    sell_price=None,
):
    """Log a trade (real or dry run) to local file."""
    from datetime import datetime
    record = {
        "timestamp": datetime.now().isoformat(),
        "market_id": market_id,
        "market_question": market_question[:100] if market_question else None,
        "bucket": bucket_label,
        "price": price,
        "amount_usd": amount,
        "shares": shares,
        "action": action,
        "mode": "dry_run" if dry_run else "live",
        "trade_id": trade_id,
        "error": error,
        "projected_count": projected_count,
        "current_count": current_count,
        "cluster_cost": cluster_cost,
        "pnl": pnl,
        # 增强字段
        "sell_reason": sell_reason,
        "sell_price": sell_price,
    }
    save_trade_record(record)
    return record


def execute_sell(market_id, shares):
    """Execute a sell trade with source tagging."""
    try:
        result = get_client().trade(
            market_id=market_id,
            side="yes",
            action="sell",
            shares=shares,
            source=TRADE_SOURCE,
        )
        return {
            "success": result.success,
            "trade_id": result.trade_id,
            "error": result.error,
        }
    except Exception as e:
        return {"error": str(e)}


def search_markets(query):
    """Search Simmer for markets matching a query."""
    try:
        # Try the API endpoint first
        data = get_client()._request("GET", "/api/sdk/markets", params={
            "q": query, "status": "active", "limit": 100
        })
        markets = data.get("markets", [])
        if markets:
            return markets
    except Exception:
        pass
    
    # Fallback: try importing known Elon tweet events and get their markets
    elon_events = [
        "https://polymarket.com/event/elon-musk-of-tweets-february-27-march-6",
        "https://polymarket.com/event/elon-musk-of-tweets-february-24-march-3",
    ]
    
    all_markets = []
    for event_url in elon_events:
        try:
            result = import_event(event_url)
            if result and "markets" in result:
                all_markets.extend(result["markets"])
        except Exception:
            continue
    
    return all_markets


def import_event(polymarket_url):
    """Import a multi-outcome event from Polymarket."""
    try:
        return get_client().import_market(polymarket_url)
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# Safeguards (reused from weather trader pattern)
# =============================================================================

def check_context_safeguards(context):
    """Check context for safeguards. Returns (should_trade, reasons)."""
    if not context:
        return True, []

    reasons = []
    market = context.get("market", {})
    warnings = context.get("warnings", [])
    discipline = context.get("discipline", {})
    slippage = context.get("slippage", {})

    for warning in warnings:
        if "MARKET RESOLVED" in str(warning).upper():
            return False, ["Market already resolved"]

    warning_level = discipline.get("warning_level", "none")
    if warning_level == "severe":
        return False, [f"Severe flip-flop warning: {discipline.get('flip_flop_warning', '')}"]
    elif warning_level == "mild":
        reasons.append("Mild flip-flop warning (proceed with caution)")

    time_str = market.get("time_to_resolution", "")
    if time_str:
        try:
            hours = 0
            if "d" in time_str:
                hours += int(time_str.split("d")[0].strip()) * 24
            if "h" in time_str:
                h_part = time_str.split("h")[0]
                if "d" in h_part:
                    h_part = h_part.split("d")[-1].strip()
                hours += int(h_part)
            if hours < TIME_TO_RESOLUTION_MIN_HOURS:
                return False, [f"Resolves in {hours}h - too soon"]
        except (ValueError, IndexError):
            pass

    estimates = slippage.get("estimates", []) if slippage else []
    if estimates:
        slippage_pct = estimates[0].get("slippage_pct", 0)
        if slippage_pct > SLIPPAGE_MAX_PCT:
            return False, [f"Slippage too high: {slippage_pct:.1%}"]

    return True, reasons


def calculate_position_size(default_size, smart_sizing):
    if not smart_sizing:
        return default_size
    portfolio = get_portfolio()
    if not portfolio:
        return default_size
    balance = portfolio.get("balance_usdc", 0)
    if balance <= 0:
        return default_size
    smart_size = min(balance * SMART_SIZING_PCT, MAX_POSITION_USD)
    smart_size = max(smart_size, MIN_POSITION_USD)
    print(f"  💡 Smart sizing: ${smart_size:.2f} ({SMART_SIZING_PCT:.0%} of ${balance:.2f})")
    return smart_size


# =============================================================================
# Core strategy
# =============================================================================

def find_target_buckets(markets, projected_count, spread=None):
    """
    Find the bucket containing the projected count and its neighbors.
    Returns list of (market, range_low, range_high, distance_from_projection).
    """
    if spread is None:
        spread = BUCKET_SPREAD
    buckets = []
    for m in markets:
        # Try outcome_name first, then question
        text = m.get("outcome_name") or m.get("question", "")
        r = parse_tweet_range(text)
        if not r:
            continue
        low, high = r
        price = m.get("external_price_yes") or m.get("current_probability") or 0.5
        buckets.append({
            "market": m,
            "low": low,
            "high": high,
            "price": price,
            "midpoint": (low + high) / 2,
        })

    if not buckets:
        return []

    # Sort by range
    buckets.sort(key=lambda b: b["low"])

    # Find the bucket containing the projection
    center_idx = None
    for i, b in enumerate(buckets):
        if b["low"] <= projected_count <= b["high"]:
            center_idx = i
            break

    # If projection doesn't land in any bucket, find nearest
    if center_idx is None:
        center_idx = min(range(len(buckets)),
                         key=lambda i: abs(buckets[i]["midpoint"] - projected_count))

    # Select center ± spread
    start = max(0, center_idx - spread)
    end = min(len(buckets), center_idx + spread + 1)

    return buckets[start:end]


def evaluate_cluster(target_buckets):
    """
    Evaluate if a cluster of buckets is +EV.
    Returns (is_profitable, total_cost, expected_profit).
    One bucket always resolves YES = $1, so if total cost < $1, it's +EV.
    """
    total_cost = sum(b["price"] for b in target_buckets)
    expected_profit = 1.0 - total_cost
    return total_cost < MAX_BUCKET_SUM, total_cost, expected_profit


# =============================================================================
# Exit strategy
# =============================================================================

def check_exit_opportunities(dry_run=True, use_safeguards=True):
    """Check open tweet positions for exit opportunities."""
    positions = get_positions()
    if not positions:
        return 0, 0

    tweet_positions = []
    for pos in positions:
        sources = pos.sources or []
        question = (pos.question or "").lower()
        if TRADE_SOURCE in sources or ("elon" in question and "tweet" in question):
            tweet_positions.append(pos)

    if not tweet_positions:
        return 0, 0

    print(f"\n📈 Checking {len(tweet_positions)} tweet positions for exit...")

    exits_found = 0
    exits_executed = 0

    for pos in tweet_positions:
        market_id = pos.market_id
        current_price = pos.current_price or 0
        shares = pos.shares_yes or 0
        question = (pos.question or "Unknown")[:50]

        if shares < MIN_SHARES_PER_ORDER:
            continue

        if current_price >= EXIT_THRESHOLD:
            exits_found += 1
            print(f"  📤 {question}...")
            print(f"     Price ${current_price:.2f} >= exit threshold ${EXIT_THRESHOLD:.2f}")

            if use_safeguards:
                context = get_market_context(market_id)
                should_trade, reasons = check_context_safeguards(context)
                if not should_trade:
                    print(f"     ⏭️  Skipped: {'; '.join(reasons)}")
                    continue

            if dry_run:
                print(f"     [DRY RUN] Would sell {shares:.1f} shares")
                # Log dry run sell
                log_trade_record(
                    market_id=market_id,
                    market_question=question,
                    bucket_label="exit",
                    price=current_price,
                    amount=shares * current_price,
                    shares=shares,
                    action="sell",
                    dry_run=True,
                    pnl=pos.pnl or 0,
                )
            else:
                print(f"     Selling {shares:.1f} shares...")
                result = execute_sell(market_id, shares)
                if result.get("success"):
                    exits_executed += 1
                    trade_id = result.get("trade_id")
                    print(f"     ✅ Sold {shares:.1f} shares @ ${current_price:.2f}")

                    # Log to local file
                    log_trade_record(
                        market_id=market_id,
                        market_question=question,
                        bucket_label="exit",
                        price=current_price,
                        amount=shares * current_price,
                        shares=shares,
                        action="sell",
                        dry_run=False,
                        trade_id=trade_id,
                        pnl=pos.pnl or 0,
                    )

                    if trade_id and JOURNAL_AVAILABLE:
                        log_trade(
                            trade_id=trade_id,
                            source=TRADE_SOURCE,
                            thesis=f"Exit: price ${current_price:.2f} reached exit threshold",
                            action="sell",
                        )
                else:
                    print(f"     ❌ Sell failed: {result.get('error', 'Unknown')}")
        else:
            print(f"  📊 {question}...")
            print(f"     Price ${current_price:.2f} < exit ${EXIT_THRESHOLD:.2f} - hold")

    return exits_found, exits_executed


# =============================================================================
# Main strategy
# =============================================================================

def run_strategy(dry_run=True, positions_only=False, show_config=False,
                 show_stats=False, smart_sizing=False, use_safeguards=True,
                 quiet=False):
    """Run the Elon tweet trading strategy."""
    def log(msg, force=False):
        if not quiet or force:
            print(msg)

    log("🐦 Simmer Elon Tweet Trader")
    log("=" * 50)

    if dry_run:
        log("\n  [DRY RUN] No trades will be executed. Use --live to enable trading.")

    log(f"\n⚙️  Configuration:")
    log(f"  Max bucket sum:  ${MAX_BUCKET_SUM:.2f} (buy cluster if total < this)")
    log(f"  Max position:    ${MAX_POSITION_USD:.2f} per bucket")
    log(f"  Bucket spread:   ±{BUCKET_SPREAD} (buy {2*BUCKET_SPREAD+1} adjacent buckets)")
    log(f"  Exit threshold:  {EXIT_THRESHOLD:.0%}")
    log(f"  Max trades/run:  {MAX_TRADES_PER_RUN}")
    log(f"  Data source:     {DATA_SOURCE}")
    log(f"  Smart sizing:    {'✓' if smart_sizing else '✗'}")
    log(f"  Safeguards:      {'✓' if use_safeguards else '✗'}")

    if show_config:
        config_path = get_config_path(__file__)
        log(f"\n  Config file: {config_path}")
        log(f"  Exists: {'Yes' if config_path.exists() else 'No'}")
        return

    # Initialize SDK client (validates API key, sets up wallet)
    get_client()

    if positions_only:
        log("\n📊 Current Tweet Positions:")
        positions = get_positions()
        tweet_pos = [p for p in positions if TRADE_SOURCE in (p.sources or [])
                     or ("elon" in (p.question or "").lower() and "tweet" in (p.question or "").lower())]
        if not tweet_pos:
            log("  No tweet positions found")
        else:
            for pos in tweet_pos:
                log(f"  • {(pos.question or 'Unknown')[:55]}...")
                pnl = pos.pnl or 0
                log(f"    YES: {pos.shares_yes or 0:.1f} | Price: {pos.current_price or 0:.2f} | P&L: ${pnl:.2f}")
        return

    # Step 1: Get XTracker data
    log("\n📡 Fetching XTracker data...")
    trackings = get_xtracker_trackings()

    if not trackings:
        log("  ⚠️  No active tracking periods found on XTracker")
        return

    log(f"  Found {len(trackings)} active tracking periods")

    tracking_stats = {}
    for t in trackings:
        stats = get_xtracker_stats(t["id"])
        if stats and stats.get("stats"):
            tracking_stats[t["id"]] = {
                "title": t.get("title", ""),
                "start": t.get("startDate"),
                "end": t.get("endDate"),
                "total": stats["stats"].get("total", 0),
                "pace": stats["stats"].get("pace", 0),
                "days_remaining": stats["stats"].get("daysRemaining", 0),
                "days_elapsed": stats["stats"].get("daysElapsed", 0),
                "percent_complete": stats["stats"].get("percentComplete", 0),
            }
            s = tracking_stats[t["id"]]
            log(f"\n  📊 {s['title'][:60]}")
            log(f"     Posts so far: {s['total']} | Projected: {s['pace']} | {s['percent_complete']}% complete")
            log(f"     Days remaining: {s['days_remaining']}")

    if show_stats:
        return

    if not tracking_stats:
        log("  ⚠️  No tracking stats available")
        return

    # Step 2: Search Simmer for Elon tweet markets
    log("\n📡 Searching for Elon tweet markets on Simmer...")
    markets = search_markets("tweets")

    # Group by event
    events = {}
    for m in markets:
        event_id = m.get("event_id") or m.get("event_ref")
        event_name = m.get("event_name", "")
        if not event_id:
            continue
        if event_id not in events:
            events[event_id] = {"name": event_name, "markets": []}
        events[event_id]["markets"].append(m)

    log(f"  Found {len(markets)} markets in {len(events)} events")

    # Step 3: If no markets found, try importing from Polymarket
    if not events:
        log("\n  No Elon tweet markets on Simmer yet. Attempting import...")
        # Use XTracker tracking titles to find Polymarket event slugs
        for tid, stats in tracking_stats.items():
            title = stats["title"]
            # Convert title to slug: "Elon Musk # tweets February 13 - February 20, 2026?"
            # → "elon-musk-of-tweets-february-13-february-20"
            # Polymarket uses "of-tweets" not "tweets", and omits the year
            slug = title.lower()
            slug = slug.replace('# tweets', 'of-tweets').replace('#tweets', 'of-tweets')
            slug = re.sub(r',?\s*\d{4}\??$', '', slug)  # Strip trailing year + question mark
            slug = re.sub(r'[?,]', '', slug)
            slug = re.sub(r'\s+', '-', slug.strip())
            slug = re.sub(r'-+', '-', slug).strip('-')

            pm_url = f"https://polymarket.com/event/{slug}"
            log(f"  Importing: {pm_url}")

            result = import_event(pm_url)
            if isinstance(result, dict) and result.get("success"):
                imported_count = result.get("markets_imported", 0)
                log(f"  ✅ Imported {imported_count} markets")
                event_id = result.get("event_id")
                if event_id and result.get("markets"):
                    events[event_id] = {
                        "name": result.get("event_name", title),
                        "markets": result["markets"],
                    }
            elif isinstance(result, dict) and result.get("already_imported"):
                log(f"  Already imported — using existing markets")
                event_id = result.get("event_id")
                if event_id and result.get("markets"):
                    events[event_id] = {
                        "name": result.get("event_name", title),
                        "markets": result["markets"],
                    }
                elif event_id:
                    # Response didn't include markets — fall back to search
                    mkt_list = search_markets(title[:50])
                    if mkt_list:
                        events[event_id] = {
                            "name": result.get("event_name", title),
                            "markets": mkt_list,
                        }
                        log(f"  Found {len(mkt_list)} existing markets via search")
                    else:
                        log(f"  ⚠️  Could not retrieve existing markets")
            else:
                error = result.get("error") if isinstance(result, dict) else str(result)
                log(f"  ⚠️  Import failed: {error}")

    if not events:
        log("\n  No Elon tweet markets available to trade.")
        return

    # Step 4: Match events to tracking periods and evaluate
    trades_executed = 0
    opportunities_found = 0

    if smart_sizing:
        portfolio = get_portfolio()
        if portfolio:
            log(f"\n💰 Balance: ${portfolio.get('balance_usdc', 0):.2f}")

    for event_id, event_data in events.items():
        event_name = event_data["name"]
        event_markets = event_data["markets"]

        # Find matching XTracker tracking
        matched_stats = None
        for tid, stats in tracking_stats.items():
            if match_tracking_to_event(stats["title"], event_name):
                matched_stats = stats
                break

        if not matched_stats:
            log(f"\n  ⚠️  No XTracker data for: {event_name[:50] if event_name else 'Unknown'}")
            continue

        projected_count = matched_stats["pace"]
        current_count = matched_stats["total"]
        pct_complete = matched_stats["percent_complete"]
        days_remaining = matched_stats["days_remaining"]

        log(f"\n🎯 {event_name[:60]}")
        log(f"   Current: {current_count} posts | Projected: {projected_count} | {pct_complete}% done")
        log(f"   Markets: {len(event_markets)}")

        # Skip future events where pace projection is unreliable
        if current_count == 0 and days_remaining > 2:
            log(f"   ⏸️  Event hasn't started yet ({current_count} posts, {days_remaining} days remaining) - projection unreliable, skipping")
            continue

        # Find target buckets around projection
        targets = find_target_buckets(event_markets, projected_count)
        if not targets:
            log(f"   ⚠️  Could not find matching buckets for projection {projected_count}")
            continue

        # Evaluate cluster profitability
        is_profitable, total_cost, expected_profit = evaluate_cluster(targets)

        bucket_names = [f"{b['low']}-{b['high']}" for b in targets]
        log(f"   Target buckets: {', '.join(bucket_names)}")
        log(f"   Cluster cost: ${total_cost:.2f} (threshold: ${MAX_BUCKET_SUM:.2f})")

        if is_profitable:
            log(f"   ✅ +EV opportunity! Expected profit: ${expected_profit:.2f} per $1 resolved")
        else:
            log(f"   ⏸️  Cluster too expensive (${total_cost:.2f} >= ${MAX_BUCKET_SUM:.2f}) - skip")
            continue

        # Trade each bucket in the cluster
        for bucket in targets:
            m = bucket["market"]
            market_id = m.get("market_id") or m.get("id")
            price = bucket["price"]
            bucket_label = f"{bucket['low']}-{bucket['high']}"

            if not market_id:
                continue

            if price < MIN_TICK_SIZE:
                log(f"   ⏸️  {bucket_label}: price ${price:.4f} below min tick - skip")
                continue
            if price > (1 - MIN_TICK_SIZE):
                log(f"   ⏸️  {bucket_label}: price ${price:.4f} too high - skip")
                continue

            # Check safeguards
            if use_safeguards:
                # Our probability: projected count landing in this bucket
                # Higher confidence for center bucket, lower for edges
                my_prob = 0.50 if bucket["low"] <= projected_count <= bucket["high"] else 0.25
                context = get_market_context(market_id, my_probability=my_prob)
                should_trade, reasons = check_context_safeguards(context)
                if not should_trade:
                    log(f"   ⏭️  {bucket_label}: {'; '.join(reasons)}")
                    continue
                if reasons:
                    log(f"   ⚠️  {bucket_label}: {'; '.join(reasons)}")

            position_size = calculate_position_size(MAX_POSITION_USD, smart_sizing)

            min_cost = MIN_SHARES_PER_ORDER * price
            if min_cost > position_size:
                log(f"   ⚠️  {bucket_label}: position ${position_size:.2f} too small for min shares at ${price:.2f}")
                continue

            if trades_executed >= MAX_TRADES_PER_RUN:
                log(f"   ⏸️  Max trades per run ({MAX_TRADES_PER_RUN}) reached")
                break

            opportunities_found += 1

            if dry_run:
                shares_est = position_size / price if price > 0 else 0
                log(f"   [DRY RUN] {bucket_label} @ ${price:.2f} — would buy ${position_size:.2f} (~{shares_est:.0f} shares)")
                # Log dry run to local file
                log_trade_record(
                    market_id=market_id,
                    market_question=m.get("question", ""),
                    bucket_label=bucket_label,
                    price=price,
                    amount=position_size,
                    shares=shares_est,
                    action="buy",
                    dry_run=True,
                    projected_count=projected_count,
                    current_count=current_count,
                    cluster_cost=total_cost,
                )
            else:
                log(f"   Buying {bucket_label} @ ${price:.2f}...", force=True)
                result = execute_trade(market_id, "yes", position_size)

                if result.get("success"):
                    trades_executed += 1
                    shares = result.get("shares_bought") or result.get("shares") or 0
                    trade_id = result.get("trade_id")
                    log(f"   ✅ Bought {shares:.1f} shares of {bucket_label} @ ${price:.2f}", force=True)

                    # Log to local file
                    log_trade_record(
                        market_id=market_id,
                        market_question=m.get("question", ""),
                        bucket_label=bucket_label,
                        price=price,
                        amount=position_size,
                        shares=shares,
                        action="buy",
                        dry_run=False,
                        trade_id=trade_id,
                        projected_count=projected_count,
                        current_count=current_count,
                        cluster_cost=total_cost,
                    )

                    if trade_id and JOURNAL_AVAILABLE:
                        log_trade(
                            trade_id=trade_id,
                            source=TRADE_SOURCE,
                            thesis=f"XTracker projects {projected_count} posts, bucket {bucket_label} "
                                   f"underpriced at ${price:.2f} (cluster cost ${total_cost:.2f})",
                            confidence=round(0.7 if bucket["low"] <= projected_count <= bucket["high"] else 0.4, 2),
                            projected_count=projected_count,
                            current_count=current_count,
                        )
                else:
                    log(f"   ❌ Trade failed: {result.get('error', 'Unknown')}", force=True)
                    # Log failed trade
                    log_trade_record(
                        market_id=market_id,
                        market_question=m.get("question", ""),
                        bucket_label=bucket_label,
                        price=price,
                        amount=position_size,
                        shares=0,
                        action="buy",
                        dry_run=False,
                        error=result.get('error', 'Unknown'),
                        projected_count=projected_count,
                        current_count=current_count,
                        cluster_cost=total_cost,
                    )

    # Check exits
    exits_found, exits_executed = check_exit_opportunities(dry_run, use_safeguards)

    # Summary
    log("\n" + "=" * 50)
    total_trades = trades_executed + exits_executed
    show_summary = not quiet or total_trades > 0
    if show_summary:
        print("📊 Summary:")
        print(f"  Events analyzed:     {len(events)}")
        print(f"  Entry opportunities: {opportunities_found}")
        print(f"  Exit opportunities:  {exits_found}")
        print(f"  Trades executed:     {total_trades}")

    if dry_run and show_summary:
        print("\n  [DRY RUN MODE - no real trades executed]")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simmer Elon Tweet Trader")
    parser.add_argument("--live", action="store_true", help="Execute real trades")
    parser.add_argument("--dry-run", action="store_true", help="(Default) Show opportunities without trading")
    parser.add_argument("--positions", action="store_true", help="Show current tweet positions only")
    parser.add_argument("--stats", action="store_true", help="Show XTracker stats only")
    parser.add_argument("--config", action="store_true", help="Show current config")
    parser.add_argument("--set", action="append", metavar="KEY=VALUE",
                        help="Set config value (e.g., --set max_bucket_sum=0.85)")
    parser.add_argument("--smart-sizing", action="store_true", help="Use portfolio-based position sizing")
    parser.add_argument("--no-safeguards", action="store_true", help="Disable context safeguards")
    parser.add_argument("--quiet", "-q", action="store_true", help="Only output on trades/errors")
    parser.add_argument("--report", "-r", action="store_true", help="Show portfolio P&L report")
    parser.add_argument("--analytics", "-a", action="store_true", help="Show trading analytics")
    parser.add_argument("--status", "-s", action="store_true", help="Show full trading status (Simmer + Polymarket)")
    args = parser.parse_args()

    if args.set:
        updates = {}
        for item in args.set:
            if "=" in item:
                key, value = item.split("=", 1)
                if key in CONFIG_SCHEMA:
                    type_fn = CONFIG_SCHEMA[key].get("type", str)
                    try:
                        value = type_fn(value)
                    except (ValueError, TypeError):
                        pass
                updates[key] = value
        if updates:
            update_config(updates, __file__)
            _reload_config_globals()
            print(f"✅ Config updated: {updates}")
            print(f"   Saved to: {get_config_path(__file__)}")

    # =============================================================================
    # Enhanced: Portfolio & Analytics Commands
    # =============================================================================
    
    # =============================================================================
    # 完整交易状态报告 (Simmer + Polymarket)
    # =============================================================================
    
    def get_simmer_positions():
        """从 Simmer 获取持仓"""
        try:
            from simmer_sdk import SimmerClient
            client = SimmerClient(api_key=os.environ.get("SIMMER_API_KEY", "sk_live_REDACTED"))
            return client.get_positions()
        except Exception as e:
            print(f"⚠️ 获取Simmer数据失败: {e}")
            return []
    
    def print_full_status_report():
        """打印完整交易状态报告"""
        import re
        from datetime import datetime
        
        now = datetime.now()
        
        print("=" * 70)
        print("🐦 ELON TWEET 交易状态报告")
        print(f"📅 生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # ==========================================================================
        # 第一部分: SIMMER 模拟盘
        # ==========================================================================
        print("\n" + "🔵 " + "=" * 66)
        print("🔵 SIMMER 模拟盘 (Dry Run)")
        print("=" * 70)
        
        try:
            from simmer_sdk import SimmerClient
            client = SimmerClient(api_key=os.environ.get("SIMMER_API_KEY", "sk_live_REDACTED"))
            positions = client.get_positions()
            
            if not positions:
                print("  ⏳ 暂无持仓")
            else:
                # 按市场分组
                markets = {}
                for pos in positions:
                    q = pos.question
                    if 'March 3 to March 10' in q:
                        market_name = 'Mar 3-10 (进行中)'
                    elif 'February 27 to March 6' in q:
                        market_name = 'Feb 27-Mar 6 (已结算)'
                    elif 'March 2 to March 4' in q:
                        market_name = 'Mar 2-4 (已结算)'
                    else:
                        market_name = '其他市场'
                    
                    if market_name not in markets:
                        markets[market_name] = []
                    markets[market_name].append(pos)
                
                simmer_invested = 0
                simmer_value = 0
                simmer_pnl = 0
                
                for market_name, poss in markets.items():
                    market_cost = 0
                    market_value = 0
                    market_pnl = 0
                    
                    print(f"\n  📅 {market_name}")
                    print("  " + "-" * 66)
                    print(f"  {'桶区间':<12} {'股数':<10} {'成本':<10} {'当前价':<10} {'当前价值':<12} {'P&L':<12}")
                    print("  " + "-" * 66)
                    
                    for pos in poss:
                        bucket = 'unknown'
                        match = re.search(r'(\d+)-(\d+)', pos.question)
                        if match:
                            bucket = f"{match.group(1)}-{match.group(2)}"
                        
                        print(f"  {bucket:<12} {pos.shares_yes:<10.2f} ${pos.cost_basis:<9.2f} ${pos.current_price:<9.3f} ${pos.current_value:<11.2f} ${pos.pnl:<+11.2f}")
                        
                        market_cost += pos.cost_basis
                        market_value += pos.current_value
                        market_pnl += pos.pnl
                    
                    print("  " + "-" * 66)
                    print(f"  {'小计':<12} {'':<10} ${market_cost:<9.2f} {'':<10} ${market_value:<11.2f} ${market_pnl:<+11.2f}")
                    
                    simmer_invested += market_cost
                    simmer_value += market_value
                    simmer_pnl += market_pnl
                
                print("\n  " + "=" * 66)
                print("  💰 SIMMER 总计:")
                print(f"     投入本金: ${simmer_invested:>10.2f}")
                print(f"     当前价值: ${simmer_value:>10.2f}")
                print(f"     总盈亏:   ${simmer_pnl:>+10.2f} ({simmer_pnl/simmer_invested*100:>+.1f}%)")
                print("  " + "=" * 66)
                
        except Exception as e:
            print(f"  ⚠️ 获取Simmer数据失败: {e}")
        
        # ==========================================================================
        # 第二部分: POLYMARKET 实盘
        # ==========================================================================
        print("\n" + "🟢 " + "=" * 66)
        print("🟢 POLYMARKET 实盘 (Real Trading)")
        print("=" * 70)
        
        # 加载本地交易记录
        local_trades = load_trades_for_analytics()
        
        # 筛选实盘交易
        live_trades = [t for t in local_trades if t.get("mode") == "live" and t.get("action") == "buy"]
        
        if not live_trades:
            print("  ⏳ 暂无实盘持仓")
        else:
            # 按市场分组
            markets = {}
            for t in live_trades:
                q = t.get("market_question", "Unknown")
                if "March 3 to March 10" in q:
                    market_name = "Mar 3-10 (进行中)"
                else:
                    market_name = "其他市场"
                
                if market_name not in markets:
                    markets[market_name] = []
                markets[market_name].append(t)
            
            poly_invested = 0
            poly_value = 0
            
            for market_name, trades in markets.items():
                market_cost = 0
                market_value = 0
                
                print(f"\n  📅 {market_name}")
                print("  " + "-" * 66)
                print(f"  {'桶区间':<12} {'股数':<10} {'买入价':<10} {'成本':<10} {'当前价':<10} {'当前价值':<12} {'P&L':<12}")
                print("  " + "-" * 66)
                
                for t in trades:
                    bucket = t.get("bucket", "unknown")
                    shares = t.get("shares", 0)
                    cost = t.get("amount_usd", 0)
                    buy_price = t.get("price", 0)
                    current_price = t.get("current_price", buy_price)
                    current_val = shares * current_price
                    pnl = current_val - cost
                    
                    print(f"  {bucket:<12} {shares:<10.2f} ${buy_price:<9.3f} ${cost:<9.2f} ${current_price:<9.3f} ${current_val:<11.2f} ${pnl:<+11.2f}")
                    
                    market_cost += cost
                    market_value += current_val
                
                print("  " + "-" * 66)
                print(f"  {'小计':<12} {'':<10} {'':<10} ${market_cost:<9.2f} {'':<10} ${market_value:<11.2f} ${market_value-market_cost:<+11.2f}")
                
                poly_invested += market_cost
                poly_value += market_value
            
            poly_pnl = poly_value - poly_invested
            
            print("\n  " + "=" * 66)
            print("  💰 POLYMARKET 总计:")
            print(f"     投入本金: ${poly_invested:>10.2f}")
            print(f"     当前价值: ${poly_value:>10.2f}")
            print(f"     总盈亏:   ${poly_pnl:>+10.2f} ({poly_pnl/poly_invested*100:>+.1f}%)" if poly_invested > 0 else "     总盈亏:   $0.00")
            print("  " + "=" * 66)
        
        # ==========================================================================
        # 第三部分: 汇总
        # ==========================================================================
        print("\n" + "=" * 70)
        print("📊 【总体汇总 ALL SUMMARY】")
        print("=" * 70)
        
        # 计算汇总
        try:
            from simmer_sdk import SimmerClient
            client = SimmerClient(api_key=os.environ.get("SIMMER_API_KEY", "sk_live_REDACTED"))
            positions = client.get_positions()
            simmer_invested = sum(p.cost_basis for p in positions)
            simmer_value = sum(p.current_value for p in positions)
        except:
            simmer_invested = simmer_value = simmer_pnl = 0
        
        poly_invested = sum(t.get("amount_usd", 0) for t in local_trades if t.get("mode") == "live" and t.get("action") == "buy")
        poly_value = sum(t.get("shares", 0) * t.get("current_price", t.get("price", 0)) for t in local_trades if t.get("mode") == "live" and t.get("action") == "buy")
        poly_pnl = poly_value - poly_invested
        
        total_invested = simmer_invested + poly_invested
        total_value = simmer_value + poly_value
        total_pnl = simmer_pnl + poly_pnl
        
        # 计算百分比
        simmer_pnl_pct = (simmer_pnl / simmer_invested * 100) if simmer_invested > 0 else 0
        poly_pnl_pct = (poly_pnl / poly_invested * 100) if poly_invested > 0 else 0
        total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        print("""
  +------------------------------------------------------------------+
  |                     SIMMER 模拟盘                               |
  +------------------------------------------------------------------+
  |  投入本金:   ${:>10.2f}                               |
  |  当前价值:   ${:>10.2f}                               |
  |  总盈亏:     ${:>+10.2f}  ({:>+.1f}%)                    |
  +------------------------------------------------------------------+
  |                     POLYMARKET 实盘                             |
  +------------------------------------------------------------------+
  |  投入本金:   ${:>10.2f}                               |
  |  当前价值:   ${:>10.2f}                               |
  |  总盈亏:     ${:>+10.2f}  ({:>+.1f}%)                    |
  +------------------------------------------------------------------+
  |                        全部总计                                 |
  +------------------------------------------------------------------+
  |  总投入本金:   ${:>10.2f}                               |
  |  当前总价值:   ${:>10.2f}                               |
  |  总盈亏:       ${:>+10.2f}  ({:>+.1f}%)                    |
  +------------------------------------------------------------------+
        """.format(
            simmer_invested, simmer_value, simmer_pnl, simmer_pnl_pct,
            poly_invested, poly_value, poly_pnl, poly_pnl_pct,
            total_invested, total_value, total_pnl, total_pnl_pct
        ))
        
        # 卖出信号检查
        print("\n🚨 卖出信号检查:")
        print("-" * 70)
        
        has_signal = False
        
        # 检查 Polymarket 实盘
        for t in live_trades:
            current_price = t.get("current_price", t.get("price", 0))
            if current_price >= 0.30:
                has_signal = True
                action = "强制卖出" if current_price >= 0.80 else "建议卖出" if current_price >= 0.50 else "关注"
                print(f"  🟢 Polymarket - 桶 {t.get('bucket')}: {current_price:.0%} → {action}")
        
        # 检查 Simmer
        try:
            from simmer_sdk import SimmerClient
            client = SimmerClient(api_key=os.environ.get("SIMMER_API_KEY", "sk_live_REDACTED"))
            for pos in client.get_positions():
                if pos.current_price >= 0.30:
                    has_signal = True
                    bucket = re.search(r'(\d+)-(\d+)', pos.question)
                    bucket = bucket.group(0) if bucket else "unknown"
                    action = "强制卖出" if pos.current_price >= 0.80 else "建议卖出" if pos.current_price >= 0.50 else "关注"
                    print(f"  🔵 Simmer - 桶 {bucket}: {pos.current_price:.0%} → {action}")
        except:
            pass
        
        if not has_signal:
            print("  ⏳ 暂无卖出信号 (所有持仓价格 < 30%)")
        
        print("\n" + "=" * 70)
        print("报告生成完毕 | 使用 --status 查看完整状态")
        print("=" * 70)
    
    # 加载持仓报告和分析的函数
    def load_trades_for_analytics():
        """加载交易记录"""
        return load_trade_log()
    
    def generate_portfolio_report():
        """生成持仓报告"""
        trades = load_trades_for_analytics()
        if not trades:
            print("暂无持仓")
            return None
        
        # 从信号文件获取当前价格
        current_prices = {}
        signal_file = os.path.expanduser("~/.openclaw/workspace/trading_logs/elon_signals.json")
        if os.path.exists(signal_file):
            try:
                with open(signal_file, "r") as f:
                    signals = json.load(f)
                    if signals and "buckets" in signals[0]:
                        for b in signals[0]["buckets"]:
                            current_prices[b["bucket"]] = b["price"]
            except:
                pass
        
        # 按bucket分组计算持仓
        position_map = {}
        for trade in trades:
            if trade.get("mode") == "live" and trade.get("action") == "buy":
                bucket = trade.get("bucket")
                if bucket not in position_map:
                    position_map[bucket] = {"shares": 0, "cost": 0}
                position_map[bucket]["shares"] += trade.get("shares", 0)
                position_map[bucket]["cost"] += trade.get("amount_usd", 0)
        
        # 计算盈亏
        positions = []
        total_invested = 0
        total_value = 0
        
        for bucket, pos in position_map.items():
            if pos["shares"] > 0:
                current_price = current_prices.get(bucket, 0)
                current_value = pos["shares"] * current_price
                pnl = current_value - pos["cost"]
                pnl_pct = (pnl / pos["cost"] * 100) if pos["cost"] > 0 else 0
                
                positions.append({
                    "bucket": bucket,
                    "shares": pos["shares"],
                    "cost": pos["cost"],
                    "current_price": current_price,
                    "current_value": current_value,
                    "pnl": pnl,
                    "pnl_percent": pnl_pct,
                })
                total_invested += pos["cost"]
                total_value += current_value
        
        return {
            "positions": positions,
            "total_invested": total_invested,
            "total_value": total_value,
            "total_pnl": total_value - total_invested,
            "total_pnl_percent": ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0,
        }
    
    def generate_analytics():
        """生成分析报告"""
        trades = load_trades_for_analytics()
        if not trades:
            print("暂无交易记录")
            return None
        
        from datetime import datetime, timedelta
        
        now = datetime.now()
        today = now.date()
        
        # 统计
        stats = {
            "total_trades": len(trades),
            "buy_trades": 0,
            "sell_trades": 0,
            "dry_run": 0,
            "live": 0,
            "total_invested": 0,
            "today_trades": 0,
            "week_trades": 0,
            "month_trades": 0,
            "markets": set(),
            "buckets": set(),
        }
        
        for t in trades:
            try:
                trade_date = datetime.fromisoformat(t["timestamp"]).date()
            except:
                trade_date = today
            
            if t.get("action") == "buy":
                stats["buy_trades"] += 1
                if t.get("mode") == "live":
                    stats["total_invested"] += t.get("amount_usd", 0)
            
            if t.get("action") == "sell":
                stats["sell_trades"] += 1
            
            if t.get("mode") == "dry_run":
                stats["dry_run"] += 1
            else:
                stats["live"] += 1
            
            if trade_date == today:
                stats["today_trades"] += 1
            
            if (now - datetime.combine(trade_date, datetime.min.time())).days <= 7:
                stats["week_trades"] += 1
            
            if (now - datetime.combine(trade_date, datetime.min.time())).days <= 30:
                stats["month_trades"] += 1
            
            if t.get("market_question"):
                stats["markets"].add(t["market_question"][:50])
            if t.get("bucket"):
                stats["buckets"].add(t["bucket"])
        
        stats["markets"] = len(stats["markets"])
        stats["buckets"] = len(stats["buckets"])
        
        return stats
    
    # 处理 --report 参数
    if hasattr(args, 'report') and args.report:
        report = generate_portfolio_report()
        if report:
            print("=" * 50)
            print("📊 Elon Tweet 持仓报告")
            print("=" * 50)
            
            if report["positions"]:
                print(f"\n{'桶区间':<12} {'股数':<8} {'成本':<8} {'当前价':<8} {'价值':<8} {'盈亏':<12}")
                print("-" * 60)
                for p in report["positions"]:
                    print(f"{p['bucket']:<12} {p['shares']:<8.2f} ${p['cost']:<7.2f} ${p.get('current_price', 0):<7.2f} ${p['current_value']:<7.2f} ${p['pnl']:<+10.2f} ({p['pnl_percent']:+.1f}%)")
                print("-" * 60)
                print(f"总计: 投入 ${report['total_invested']:.2f} | 当前 ${report['total_value']:.2f} | 盈亏 ${report['total_pnl']:+.2f} ({report['total_pnl_percent']:+.1f}%)")
            
            # 检查卖出信号
            if report["positions"]:
                print("\n🚨 卖出信号:")
                has_signal = False
                for p in report["positions"]:
                    price = p.get("current_price", 0)
                    if price >= 0.30:
                        has_signal = True
                        action = "强制卖出" if price >= 0.80 else "建议卖出" if price >= 0.50 else "关注"
                        print(f"   • 桶 {p['bucket']}: {price:.0%} → {action}")
                if not has_signal:
                    print("   ⏳ 暂无卖出信号 (价格 < 30%)")
    
    # 处理 --status 参数 (完整交易状态报告)
    elif hasattr(args, 'status') and args.status:
        print_full_status_report()
    
    # 处理 --analytics 参数
    elif hasattr(args, 'analytics') and args.analytics:
        stats = generate_analytics()
        if stats:
            print("=" * 50)
            print("📈 Elon Tweet 交易分析")
            print("=" * 50)
            print(f"\n📊 总交易: {stats['total_trades']}")
            print(f"   买入: {stats['buy_trades']} | 卖出: {stats['sell_trades']}")
            print(f"   实盘: {stats['live']} | 模拟: {stats['dry_run']}")
            print(f"   总投入: ${stats['total_invested']:.2f}")
            print(f"\n📅 今日交易: {stats['today_trades']}")
            print(f"📆 本周交易: {stats['week_trades']}")
            print(f"📆 本月交易: {stats['month_trades']}")
            print(f"\n🏪 涉及市场: {stats['markets']}")
            print(f"🪣 交易桶区间: {stats['buckets']}")
    
    # 默认运行策略
    else:
        dry_run = not args.live

        run_strategy(
            dry_run=dry_run,
            positions_only=args.positions,
            show_config=args.config,
            show_stats=args.stats,
            smart_sizing=args.smart_sizing,
            use_safeguards=not args.no_safeguards,
            quiet=args.quiet,
        )
