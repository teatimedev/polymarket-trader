# 🎰 Polymarket Trader - Clawdbot Skill

An autonomous Polymarket trading skill for [Clawdbot](https://github.com/clawdbot/clawdbot). Scans prediction markets, researches opportunities with AI, and executes trades when it finds edge.

## Quick Start

### 1. Install the Skill

```bash
cd ~/clawd/skills
git clone https://github.com/teatimedev/polymarket-trader.git
```

Or via ClawdHub (when published):
```bash
clawdhub install polymarket-trader
```

### 2. Set Up Python Environment

```bash
python3 -m venv ~/polymarket-venv
source ~/polymarket-venv/bin/activate
pip install py-clob-client eth-account requests
```

### 3. Configure Credentials

Add to your shell config (`~/.bashrc`):
```bash
export POLYMARKET_PRIVATE_KEY="0x..."  # Your wallet private key
export POLYMARKET_FUNDER="0x..."       # Optional: for Magic Link accounts
```

### 4. Fund Your Wallet

Deposit USDC to your Polygon wallet. Minimum $5 per trade.

### 5. Restart Clawdbot

```bash
clawdbot gateway restart
```

---

## Chat Commands

Once installed, just chat with your Clawdbot:

| You say | What happens |
|---------|--------------|
| "Scan Polymarket for opportunities" | Runs the scanner, shows top markets |
| "What's trending on Polymarket?" | Shows trending markets by volume |
| "Search Polymarket for Trump" | Searches markets matching query |
| "Check my Polymarket positions" | Shows your current positions & P&L |
| "Research the Iran strike market" | Deep research on a specific market |
| "Buy $5 of YES on [market]" | Places a trade |
| "What's my Polymarket balance?" | Shows account balance |
| "Cancel all my Polymarket orders" | Cancels open orders |

### Example Conversation

```
You: Scan polymarket for good opportunities

Clawd: 🔍 Scanning 500+ markets...

📊 TOP 5 OPPORTUNITIES

1. US strikes Iran by Feb 28 — Score: 99
   YES: 42.5% | $2.9M volume
   
2. Thai Election - People's Party — Score: 93
   YES: 61.5% | $649K volume

Want me to research any of these deeper?

You: Research the Iran one

Clawd: 🔎 Researching "US strikes Iran"...

[Pulls 8 news sources, analyzes evidence]

My estimate: 55% (market: 42.5%)
Edge: +12.5% on YES

Want me to place a trade?

You: Yes, $5 on YES

Clawd: ✅ Order placed!
BUY YES @ $0.43 | Size: $5
```

---

## Automated Trading (Cron Jobs)

Set up autonomous trading that runs in the background:

### Daily Briefing (9am)
```bash
clawdbot cron add --name "Polymarket Daily Scan" \
  --schedule "0 9 * * *" \
  --tz "Europe/London" \
  --message "Scan Polymarket and send me the top 5 opportunities"
```

### Trading Scan (every 6h)
```bash
clawdbot cron add --name "Polymarket Trader" \
  --schedule "0 */6 * * *" \
  --tz "Europe/London" \
  --message "Scan Polymarket, research top markets, trade if edge >10%"
```

### Position Monitor (every 3h)
```bash
clawdbot cron add --name "Position Monitor" \
  --schedule "30 */3 * * *" \
  --tz "Europe/London" \
  --message "Check my Polymarket positions, alert if any moved significantly"
```

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  SCAN                                               │
│  Pull 500+ active markets from Polymarket API       │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  FILTER & SCORE                                     │
│  Volume >$10k, Liquidity >$1k, Odds 10-90%         │
│  Score by uncertainty, volume, time to resolution   │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  RESEARCH (Top 2-3 markets)                         │
│  Exa AI deep search for news, expert opinions       │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  CALCULATE EDGE                                     │
│  My probability estimate vs market price            │
│  Edge = My estimate - Market price                  │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  TRADE (if edge >10%)                               │
│  Place limit order, log to memory                   │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  MONITOR                                            │
│  Track P&L, alert on moves, take profits/stop loss  │
└─────────────────────────────────────────────────────┘
```

### Scoring Algorithm (100 pts max)

| Factor | Points | Why |
|--------|--------|-----|
| Odds 20-80% | 30 | Uncertainty = edge potential |
| Volume | 25 | Credible market |
| Liquidity | 15 | Can enter/exit |
| 24h activity | 10 | Active trading |
| Resolves in 1-30 days | 20 | Sweet spot |

---

## Configuration

Edit `config.json` in the skill folder:

```json
{
  "budget": {
    "total_usd": 25,
    "max_per_trade_usd": 10,
    "daily_loss_limit_usd": 15
  },
  "strategy": {
    "min_volume_usd": 10000,
    "min_confidence": 0.7,
    "categories": ["politics", "crypto", "geopolitics"],
    "avoid_categories": ["sports"]
  }
}
```

---

## Scripts (Advanced)

For direct CLI usage:

```bash
source ~/polymarket-venv/bin/activate

# Scanner
python3 scripts/scanner.py --limit 20 --exclude-sports
python3 scripts/scanner.py -c politics -c geopolitics --json

# Markets
python3 scripts/markets.py trending
python3 scripts/markets.py search "bitcoin"
python3 scripts/markets.py detail <slug>

# Trading
python3 scripts/trade.py buy <token_id> --price 0.50 --size 5 --yes
python3 scripts/trade.py sell <token_id> --price 0.70 --size 5 --yes

# Orders
python3 scripts/orders.py list
python3 scripts/orders.py cancel <order_id>
python3 scripts/orders.py cancel-all

# Account
python3 scripts/account.py
```

---

## Requirements

- [Clawdbot](https://github.com/clawdbot/clawdbot) (any recent version)
- Python 3.10+
- Polymarket account with USDC on Polygon
- (Optional) [Exa AI](https://exa.ai) API key for research

---

## API Notes

| API | URL | Purpose |
|-----|-----|---------|
| Gamma | `https://gamma-api.polymarket.com` | Market data (read-only) |
| CLOB | `https://clob.polymarket.com` | Trading |

- Chain: Polygon (137)
- Currency: USDC
- Min order: $5

---

## ⚠️ Disclaimer

**This is real money trading.** Use at your own risk. Past performance ≠ future results. Only trade what you can afford to lose.

---

## License

MIT

---

## Links

- [Clawdbot](https://github.com/clawdbot/clawdbot) - AI agent framework
- [Polymarket](https://polymarket.com) - Prediction markets
- [py-clob-client](https://github.com/Polymarket/py-clob-client) - Python SDK
