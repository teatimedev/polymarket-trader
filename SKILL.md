---
name: polymarket-trader
description: Trade on Polymarket prediction markets - place orders, check positions, research markets with AI, and execute trading strategies.
homepage: https://polymarket.com
metadata: {"clawdbot":{"emoji":"🎰"}}
---

# Polymarket Trader

Full trading access to Polymarket prediction markets. Research markets, analyze odds, and execute trades.

## Setup

Requires environment variable:
```bash
export POLYMARKET_PRIVATE_KEY="0x..."  # Your wallet private key
export POLYMARKET_FUNDER="0x..."       # Optional: proxy/funder address for Magic Link accounts
```

Uses Python venv at `~/polymarket-venv` with `py-clob-client`.

## Commands

### Check Balance & Positions
```bash
python3 {baseDir}/scripts/account.py
```

### Search Markets
```bash
python3 {baseDir}/scripts/markets.py search "trump"
python3 {baseDir}/scripts/markets.py trending
python3 {baseDir}/scripts/markets.py category politics
```

### Get Market Details
```bash
python3 {baseDir}/scripts/markets.py detail <market_id_or_slug>
```

### Scan for Opportunities (Systematic Scanner)
```bash
# Full scan - top 25 opportunities across all categories
python3 {baseDir}/scripts/scanner.py --limit 25

# Exclude sports (focus on news/politics/crypto)
python3 {baseDir}/scripts/scanner.py --exclude-sports --limit 20

# Filter by category
python3 {baseDir}/scripts/scanner.py -c politics -c geopolitics --limit 15

# Tighter odds range (closer to 50/50 = more uncertainty)
python3 {baseDir}/scripts/scanner.py --min-odds 0.30 --max-odds 0.70

# Higher volume threshold
python3 {baseDir}/scripts/scanner.py --min-volume 50000 --min-liquidity 5000

# JSON output for programmatic use
python3 {baseDir}/scripts/scanner.py --json --limit 10
```

**Scanner Scoring (100 pts max):**
- Odds 20-80% range (30 pts) - uncertainty = edge potential
- Volume log scale (25 pts) - credible market
- 24h activity (10 pts) - live trading
- Liquidity (15 pts) - can enter/exit
- Time to resolution 1-30 days (20 pts) - sweet spot

**Categories detected:** politics, crypto, geopolitics, tech, sports, entertainment, economics, other

### Place Orders
```bash
# Buy YES at limit price (minimum $5)
python3 {baseDir}/scripts/trade.py buy <token_id> --price 0.65 --size 5

# Buy NO
python3 {baseDir}/scripts/trade.py buy <token_id> --side NO --price 0.35 --size 10

# Skip confirmation (for automated trading)
python3 {baseDir}/scripts/trade.py buy <token_id> --price 0.50 --size 5 --yes

# Market order (takes best available)
python3 {baseDir}/scripts/trade.py buy <token_id> --market --size 5

# Sell position
python3 {baseDir}/scripts/trade.py sell <token_id> --price 0.70 --size 5
```

**Note:** Minimum order size is $5 USDC.

### Manage Orders
```bash
python3 {baseDir}/scripts/orders.py list           # View open orders
python3 {baseDir}/scripts/orders.py cancel <id>    # Cancel specific order
python3 {baseDir}/scripts/orders.py cancel-all     # Cancel all orders
```

### Research Mode
For deep research before trading, use the exa-search skill:
```bash
# Research a topic before betting
mcporter call "https://mcp.exa.ai/mcp?tools=deep_search_exa" deep_search_exa query="Will the Fed cut rates in March 2026?"

# Get latest news
mcporter call "https://mcp.exa.ai/mcp?tools=web_search_advanced_exa" web_search_advanced_exa \
  query="Federal Reserve interest rate decision" \
  category="news" \
  numResults:10 \
  --args '{"startPublishedDate": "2026-01-01"}'
```

## Trading Workflow

1. **Find Market**: `markets.py search "<topic>"` or `markets.py trending`
2. **Research**: Use exa-search for deep research on the topic
3. **Analyze**: Check current odds, volume, end date
4. **Trade**: Place order with `trade.py buy/sell`
5. **Monitor**: Check positions with `account.py`

## Example Chat Usage

- "What are the trending Polymarket markets?"
- "Research and bet $50 on Trump winning 2028"
- "What's the current spread on Bitcoin hitting 100k?"
- "Cancel all my open orders"
- "What's my Polymarket balance?"
- "Do deep research on Fed rate cuts and place a bet"

## Signature Types

- `0` = EOA (MetaMask/standard wallet)
- `1` = POLY_PROXY (Magic Link email/Google login)
- `2` = GNOSIS_SAFE (multisig)

## Notes

- All trades are on Polygon mainnet (chain_id: 137)
- Funds are in USDC
- This is real money — use wisely!
- For Magic Link accounts: you may need to find your proxy address on polymarket.com
