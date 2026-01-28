# Polymarket Trader Skill for Clawdbot

An autonomous Polymarket trading system that scans markets, researches opportunities, and executes trades based on calculated edge.

## Features

- **Market Scanner**: Systematically scans 500+ active markets and ranks by opportunity score
- **Research Integration**: Uses Exa AI for deep research on market topics
- **Edge Calculation**: Compares market odds to researched probability estimates
- **Automated Trading**: Places limit orders when edge threshold is met
- **Position Monitoring**: Tracks P&L and alerts on significant moves
- **Memory System**: Logs all trades, research, and lessons learned

## How It Works

```
SCAN (500+ markets)
    ↓ filter by volume, liquidity, odds
TOP OPPORTUNITIES (scored 0-100)
    ↓ pick top 2-3
RESEARCH (Exa deep search)
    ↓ gather evidence, form probability
EDGE > 10%?
    ↓ yes
PLACE TRADE → LOG → MONITOR
```

### Scoring Algorithm (100 pts max)

| Factor | Points | Rationale |
|--------|--------|-----------|
| Odds uncertainty (20-80%) | 30 | More uncertainty = more edge potential |
| Volume (log scale) | 25 | Higher volume = credible market |
| Liquidity | 15 | Can enter/exit positions |
| 24h activity | 10 | Active trading = live market |
| Time to resolution (1-30d) | 20 | Sweet spot for research + resolution |

## Installation

### Prerequisites

- [Clawdbot](https://github.com/clawdbot/clawdbot) installed and running
- Python 3.10+
- Polymarket account with USDC balance

### 1. Install the skill

```bash
# Clone to your Clawdbot skills directory
cd ~/clawd/skills
git clone https://github.com/YOUR_USERNAME/polymarket-trader.git
```

### 2. Set up Python environment

```bash
# Create virtual environment
python3 -m venv ~/polymarket-venv
source ~/polymarket-venv/bin/activate

# Install dependencies
pip install py-clob-client eth-account requests
```

### 3. Configure environment variables

```bash
# Add to ~/.bashrc or your shell config
export POLYMARKET_PRIVATE_KEY="0x..."  # Your wallet private key
export POLYMARKET_FUNDER="0x..."       # Optional: proxy address for Magic Link accounts
```

**Getting your private key:**
- **MetaMask**: Settings → Security → Reveal Private Key
- **Magic Link**: Find your proxy address on polymarket.com account settings

### 4. Fund your wallet

Deposit USDC to your Polygon wallet address. Minimum $5 per trade.

## Usage

### Manual Commands

```bash
source ~/polymarket-venv/bin/activate

# Check account balance and positions
python3 scripts/account.py

# Scan for opportunities
python3 scripts/scanner.py --limit 20 --exclude-sports

# Search specific markets
python3 scripts/markets.py search "trump"
python3 scripts/markets.py trending
python3 scripts/markets.py detail <slug>

# Place a trade
python3 scripts/trade.py buy <token_id> --price 0.50 --size 5 --yes

# Manage orders
python3 scripts/orders.py list
python3 scripts/orders.py cancel <order_id>
python3 scripts/orders.py cancel-all
```

### Scanner Options

```bash
# Full scan excluding sports
python3 scripts/scanner.py --exclude-sports --limit 30

# Filter by category
python3 scripts/scanner.py -c politics -c geopolitics

# Tighter odds range (closer to 50/50)
python3 scripts/scanner.py --min-odds 0.30 --max-odds 0.70

# Higher volume threshold
python3 scripts/scanner.py --min-volume 50000

# JSON output
python3 scripts/scanner.py --json --limit 10
```

### Automated Trading (Cron Jobs)

Set up Clawdbot cron jobs for autonomous operation:

**Daily Market Scan (9am)**
```json
{
  "name": "Polymarket Daily Scan",
  "schedule": { "kind": "cron", "expr": "0 9 * * *", "tz": "Europe/London" },
  "payload": {
    "message": "Run market scan and report top 5 opportunities..."
  }
}
```

**Trading Scan (every 6h)**
```json
{
  "name": "Polymarket Trader",
  "schedule": { "kind": "cron", "expr": "0 */6 * * *", "tz": "Europe/London" },
  "payload": {
    "message": "Scan markets, research top picks, execute trades if edge found..."
  }
}
```

**Position Monitor (every 3h)**
```json
{
  "name": "Position Monitor",
  "schedule": { "kind": "cron", "expr": "30 */3 * * *", "tz": "Europe/London" },
  "payload": {
    "message": "Check positions, alert on significant moves..."
  }
}
```

## Configuration

Edit `config.json` to customize:

```json
{
  "budget": {
    "total_usd": 25,
    "max_per_trade_usd": 10,
    "daily_loss_limit_usd": 15,
    "min_position_usd": 2
  },
  "strategy": {
    "max_expiry_days": 7,
    "min_expiry_hours": 6,
    "min_volume_usd": 10000,
    "min_confidence": 0.7,
    "categories": ["politics", "crypto", "business", "science"],
    "avoid_categories": ["sports"]
  }
}
```

## Trading Workflow

1. **Scanner** pulls all active markets from Polymarket Gamma API
2. **Filter** by volume ($10k+), liquidity ($1k+), odds (10-90%)
3. **Score** each market (uncertainty, volume, liquidity, time)
4. **Research** top opportunities using Exa AI search
5. **Estimate** true probability based on evidence
6. **Calculate edge**: Your estimate - Market price
7. **Trade** if edge > 10% threshold
8. **Log** trade details, thesis, and reasoning to memory
9. **Monitor** positions for profit-taking or stop-loss

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `scanner.py` | Systematic market scanner with scoring |
| `markets.py` | Search, trending, category, and detail queries |
| `trade.py` | Place buy/sell orders |
| `orders.py` | List and cancel open orders |
| `account.py` | Check balance and positions |
| `auto_trader.py` | Autonomous trading logic (used by crons) |

## API Notes

- **Gamma API** (read-only): `https://gamma-api.polymarket.com`
- **CLOB API** (trading): `https://clob.polymarket.com`
- Trades on **Polygon mainnet** (chain_id: 137)
- Funds in **USDC**
- Minimum order size: **$5**

## Signature Types

| Type | Value | Use Case |
|------|-------|----------|
| EOA | 0 | MetaMask, standard wallets |
| POLY_PROXY | 1 | Magic Link (email/Google login) |
| GNOSIS_SAFE | 2 | Multisig wallets |

## Disclaimer

⚠️ **This is real money trading.** Use at your own risk. Past performance does not guarantee future results. Only trade what you can afford to lose.

## License

MIT

## Credits

Built for [Clawdbot](https://github.com/clawdbot/clawdbot) - the AI agent framework.

Uses:
- [Polymarket](https://polymarket.com) CLOB & Gamma APIs
- [py-clob-client](https://github.com/Polymarket/py-clob-client)
- [Exa AI](https://exa.ai) for research
