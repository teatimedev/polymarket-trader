# 🎰 Polymarket Trader - Clawdbot Skill

An autonomous Polymarket trading skill for [Clawdbot](https://github.com/clawdbot/clawdbot). Scans prediction markets, researches opportunities with AI, and executes trades when it finds edge.

## Quick Start

### 1. Install the Skill

```bash
cd ~/clawd/skills
git clone https://github.com/teatimedev/polymarket-trader.git
```

### 2. Configure Credentials

Add to `~/.bashrc`:
```bash
# Required: Polymarket wallet
export POLYMARKET_PRIVATE_KEY="0x..."  # Your wallet private key

# Required: Exa AI for research
export EXA_API_KEY="..."  # Get from https://exa.ai
```

Then reload: `source ~/.bashrc`

**Get your Exa API key:** https://dashboard.exa.ai/api-keys (free tier available)

### 3. Set Up via Chat

Just tell your Clawdbot:

> **"Set up Polymarket trading"**

This automatically:
- ✅ Creates Python virtual environment
- ✅ Installs dependencies (py-clob-client, etc.)
- ✅ Sets up 3 cron jobs for autonomous trading
- ✅ Verifies your configuration

**That's it!** No terminal commands needed after the initial clone.

---

## Chat Commands

| You say | What happens |
|---------|--------------|
| **"Set up Polymarket trading"** | Auto-configures everything |
| "Scan Polymarket" | Shows top opportunities with scores |
| "Polymarket trending" | Shows markets by volume |
| "Search Polymarket for bitcoin" | Searches markets |
| "Check my Polymarket positions" | Shows positions & P&L |
| "Check my Polymarket balance" | Shows account balance |
| "Research [market topic]" | Deep research + edge calculation |
| "Buy $5 of YES on [market]" | Places a trade |
| "Cancel my Polymarket orders" | Cancels open orders |

### Example: Full Trading Flow

```
You: Set up Polymarket trading

Clawd: 🎰 Setting up Polymarket Trader...
✓ Python environment ready
✓ Created 3 cron jobs:
  - Daily Scan (9am) - morning briefing
  - Trader (every 6h) - research & execute
  - Position Monitor (every 3h) - track P&L

You're all set! Say "Scan Polymarket" to find opportunities.

---

You: Scan Polymarket

Clawd: 🔍 Scanning 500+ markets...

📊 TOP 5 OPPORTUNITIES

1. US strikes Iran by Feb 28 — Score: 99
   YES: 42.5% | $2.9M volume
   
2. Thai Election - People's Party — Score: 93
   YES: 61.5% | $649K volume

Want me to research any of these?

---

You: Research the Iran one

Clawd: 🔎 Researching...

Found 8 sources:
- USS Lincoln carrier arrived in region
- Trump: "armada floating toward Iran"
- Iran: "finger on the trigger"

My estimate: 55% | Market: 42.5%
Edge: +12.5% on YES ✅

Want me to trade?

---

You: Yes, buy $5

Clawd: ✅ Order placed!
BUY YES @ $0.43 | Size: $5

If YES wins: $5 → $11.63 (+$6.63)
Logged to memory.
```

---

## What Gets Automated

After setup, these run automatically:

| Cron | Schedule | What it does |
|------|----------|--------------|
| **Daily Scan** | 9am | Morning briefing with top 5 opportunities |
| **Trader** | Every 6h | Scan → Research → Trade if edge >10% |
| **Position Monitor** | Every 3h | Track P&L, alert on big moves |

All crons:
- Read/write to memory (continuous context)
- Run in isolated sessions
- Only message you when something matters

---

## How It Works

```
┌─────────────────────────────────────────────────────┐
│  SCAN — Pull 500+ markets from Polymarket           │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  FILTER & SCORE                                     │
│  • Volume >$10k  • Liquidity >$1k  • Odds 10-90%   │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  RESEARCH — Exa AI search for news & evidence       │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  CALCULATE EDGE — My probability vs market price    │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  TRADE — If edge >10%, place limit order            │
└─────────────────┬───────────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────────┐
│  MONITOR — Track P&L, profits, stop-losses          │
└─────────────────────────────────────────────────────┘
```

### Scoring (100 pts max)

| Factor | Points | Why |
|--------|--------|-----|
| Odds 20-80% | 30 | Uncertainty = edge potential |
| Volume | 25 | Credible market |
| Liquidity | 15 | Can enter/exit |
| 24h activity | 10 | Active trading |
| Resolves 1-30 days | 20 | Sweet spot |

### Research (Exa AI)

When you say "Research [topic]", Clawdbot uses Exa MCP to:

1. **News Search** — Recent articles (last 7 days)
   ```
   mcporter call "https://mcp.exa.ai/mcp" web_search_advanced_exa
     query="US Iran strikes" category="news"
   ```

2. **Evidence Gathering** — Key facts for/against

3. **Probability Estimate** — Based on evidence

4. **Edge Calculation** — Your estimate vs market price

Example output:
```
📰 Found 8 sources:
- CNN: "US carrier enters Middle East"
- Reuters: "Trump hints at diplomacy"

⚖️ Evidence:
FOR (strike likely): Military buildup, past precedent
AGAINST: Diplomatic signals, international pressure

📊 My estimate: 55% | Market: 42%
✅ Edge: +13% on YES
```

---

## Configuration

Edit `config.json` to customize:

```json
{
  "budget": {
    "total_usd": 25,
    "max_per_trade_usd": 10,
    "daily_loss_limit_usd": 15
  },
  "strategy": {
    "min_volume_usd": 10000,
    "categories": ["politics", "crypto", "geopolitics"],
    "avoid_categories": ["sports"]
  }
}
```

---

## Manual Setup (Alternative)

If you prefer terminal:

```bash
# Run the setup script
cd ~/clawd/skills/polymarket-trader
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
# Create venv
python3 -m venv ~/polymarket-venv
source ~/polymarket-venv/bin/activate
pip install py-clob-client eth-account requests

# Add crons via Clawdbot CLI
clawdbot cron add --name "Polymarket Daily Scan" --schedule "0 9 * * *" ...
```

---

## Requirements

- [Clawdbot](https://github.com/clawdbot/clawdbot)
- Python 3.10+
- Polymarket account with USDC on Polygon
- [Exa AI](https://exa.ai) API key for research (free tier available)

### Getting API Keys

| Service | URL | Notes |
|---------|-----|-------|
| Polymarket | [polymarket.com](https://polymarket.com) | Export private key from wallet |
| Exa AI | [dashboard.exa.ai](https://dashboard.exa.ai/api-keys) | Free tier: 1000 searches/month |

---

## ⚠️ Disclaimer

**Real money trading.** Use at your own risk. Only trade what you can afford to lose.

---

## License

MIT

---

## Links

- [Clawdbot](https://github.com/clawdbot/clawdbot) - AI agent framework
- [Polymarket](https://polymarket.com) - Prediction markets
- [ClawdHub](https://clawdhub.com) - Skill marketplace
