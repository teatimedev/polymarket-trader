---
name: polymarket-trader
description: Trade on Polymarket prediction markets - scan opportunities, research with AI, place orders, monitor positions. Say "Set up Polymarket trading" to auto-configure.
homepage: https://github.com/teatimedev/polymarket-trader
metadata: {"clawdbot":{"emoji":"🎰"}}
---

# Polymarket Trader

Autonomous Polymarket trading skill. Scans markets, researches opportunities, executes trades.

## Setup Command

When user says **"Set up Polymarket trading"** or **"Configure Polymarket skill"**:

1. Check if Python venv exists:
```bash
ls ~/polymarket-venv/bin/activate
```

2. If not, create it:
```bash
python3 -m venv ~/polymarket-venv
source ~/polymarket-venv/bin/activate
pip install py-clob-client eth-account requests
```

3. Create the cron jobs (use cron tool, not exec):
   - **Polymarket Daily Scan**: `0 9 * * *` Europe/London, isolated session
   - **Polymarket Trader**: `0 */6 * * *` Europe/London, isolated session  
   - **Polymarket Position Monitor**: `30 */3 * * *` Europe/London, isolated session

4. Check if `POLYMARKET_PRIVATE_KEY` is set. If not, tell user to add it to ~/.bashrc

5. Confirm setup complete and explain what each cron does.

## Chat Commands

| User says | Action |
|-----------|--------|
| "Set up Polymarket trading" | Run setup (create venv + crons) |
| "Scan Polymarket" | Run scanner.py, show top opportunities |
| "Polymarket trending" | Run markets.py trending |
| "Search Polymarket for X" | Run markets.py search "X" |
| "Check Polymarket positions" | Run account.py |
| "Check Polymarket balance" | Run account.py |
| "Buy $X on [market] YES/NO" | Research → trade.py with --yes |
| "Cancel Polymarket orders" | Run orders.py cancel-all |
| "Research [market topic]" | Exa search → form probability → compare to market |

## Scripts

All scripts require: `source ~/polymarket-venv/bin/activate`

### Scan for Opportunities
```bash
python3 {baseDir}/scripts/scanner.py --limit 30 --exclude-sports
python3 {baseDir}/scripts/scanner.py -c politics -c geopolitics --json
python3 {baseDir}/scripts/scanner.py --min-odds 0.30 --max-odds 0.70
```

### Search & Browse Markets
```bash
python3 {baseDir}/scripts/markets.py trending
python3 {baseDir}/scripts/markets.py search "trump"
python3 {baseDir}/scripts/markets.py category politics
python3 {baseDir}/scripts/markets.py detail <slug>
```

### Place Orders (min $5)
```bash
# Buy YES at limit price (--yes skips confirmation)
python3 {baseDir}/scripts/trade.py buy <token_id> --price 0.50 --size 5 --yes

# Buy NO
python3 {baseDir}/scripts/trade.py buy <token_id> --side NO --price 0.35 --size 5 --yes

# Sell position
python3 {baseDir}/scripts/trade.py sell <token_id> --price 0.70 --size 5 --yes
```

### Manage Orders
```bash
python3 {baseDir}/scripts/orders.py list
python3 {baseDir}/scripts/orders.py cancel <order_id>
python3 {baseDir}/scripts/orders.py cancel-all
```

### Check Account
```bash
python3 {baseDir}/scripts/account.py
```

## Cron Job Messages

### Daily Scan (9am)
```
Daily Polymarket opportunity scan.

## MEMORY FIRST
Read ~/clawd/memory/YYYY-MM-DD.md (last 2-3 days) for context.

## SCAN
source ~/polymarket-venv/bin/activate && python3 ~/clawd/skills/polymarket-trader/scripts/scanner.py --limit 30 --exclude-sports

## REPORT
Top 5 opportunities, time-sensitive markets, themes.
```

### Trader (every 6h)
```
Polymarket systematic trading scan.

## MEMORY FIRST
Read memory for positions, past research, lessons.

## CHECK BALANCE & SCAN
source ~/polymarket-venv/bin/activate
python3 ~/clawd/skills/polymarket-trader/scripts/account.py
python3 ~/clawd/skills/polymarket-trader/scripts/scanner.py --exclude-sports --limit 15

## RESEARCH & TRADE
Top 2-3 markets: Exa research → probability estimate → trade if edge >10%

## UPDATE MEMORY
Log trades, research, lessons.
```

### Position Monitor (every 3h)
```
Polymarket position check.

## MEMORY + CHECK
Read memory for entry prices.
source ~/polymarket-venv/bin/activate && python3 ~/clawd/skills/polymarket-trader/scripts/account.py

## ACTIONS
- Up >15% → consider profit
- Down >20% → consider stop
- Resolving <24h → flag

## UPDATE MEMORY
Log status. Only message user if notable.
```

## Research Workflow

When researching a market:
1. Use Exa deep search for recent news (last 7 days)
2. Gather evidence for and against
3. Form probability estimate
4. Compare to market price
5. Calculate edge: `My estimate - Market price`
6. Trade if edge > 10%

## Environment Variables

```bash
POLYMARKET_PRIVATE_KEY="0x..."  # Required: wallet private key
POLYMARKET_FUNDER="0x..."       # Optional: proxy address for Magic Link
```

## Notes

- Trades on Polygon mainnet (chain_id: 137)
- Funds in USDC
- Minimum order: $5
- Use `--yes` flag for automated trading (skips confirmation)
