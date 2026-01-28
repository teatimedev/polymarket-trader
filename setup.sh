#!/bin/bash
# Polymarket Trader Skill - Auto Setup
# Run this or ask Clawdbot: "Set up Polymarket trading"

set -e

echo "🎰 Setting up Polymarket Trader skill..."

# Check for Python venv
if [ ! -d "$HOME/polymarket-venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv ~/polymarket-venv
    source ~/polymarket-venv/bin/activate
    pip install py-clob-client eth-account requests
else
    echo "✓ Python venv exists"
fi

# Check for credentials
MISSING_CREDS=0

if [ -z "$POLYMARKET_PRIVATE_KEY" ]; then
    echo ""
    echo "⚠️  POLYMARKET_PRIVATE_KEY not set!"
    echo "Add to ~/.bashrc:"
    echo '  export POLYMARKET_PRIVATE_KEY="0x..."'
    MISSING_CREDS=1
fi

if [ -z "$EXA_API_KEY" ]; then
    echo ""
    echo "⚠️  EXA_API_KEY not set!"
    echo "Get your key: https://dashboard.exa.ai/api-keys"
    echo "Add to ~/.bashrc:"
    echo '  export EXA_API_KEY="..."'
    MISSING_CREDS=1
fi

if [ $MISSING_CREDS -eq 1 ]; then
    echo ""
    echo "After adding keys, run: source ~/.bashrc"
    echo ""
fi

# Create cron jobs via Clawdbot
echo "📅 Setting up cron jobs..."

# Daily Scan (9am)
clawdbot cron add \
  --name "Polymarket Daily Scan" \
  --schedule "0 9 * * *" \
  --tz "Europe/London" \
  --isolated \
  --message "Daily Polymarket opportunity scan.

## MEMORY FIRST
Read ~/clawd/memory/2026-*.md (last 2-3 days) for context.

## SCAN
source ~/polymarket-venv/bin/activate && python3 ~/clawd/skills/polymarket-trader/scripts/scanner.py --limit 30 --exclude-sports

## REPORT
Send a concise morning briefing with:
- Top 5 opportunities ranked by score
- Any time-sensitive markets (<48h)
- Current themes

Keep it punchy." 2>/dev/null && echo "✓ Daily Scan cron created" || echo "⚠ Daily Scan may already exist"

# Trading Scan (every 6h)
clawdbot cron add \
  --name "Polymarket Trader" \
  --schedule "0 */6 * * *" \
  --tz "Europe/London" \
  --isolated \
  --message "Polymarket systematic trading scan.

## MEMORY FIRST
Read ~/clawd/memory/2026-*.md for positions, past research, lessons.

## CHECK BALANCE
source ~/polymarket-venv/bin/activate && python3 ~/clawd/skills/polymarket-trader/scripts/account.py

## SCAN
python3 ~/clawd/skills/polymarket-trader/scripts/scanner.py --exclude-sports --limit 15

## RESEARCH & TRADE
For top 2-3 markets (not recently researched):
1. Use Exa to research recent news
2. Form probability estimate
3. If edge >10%, place trade (max \$10, use --yes flag)

## UPDATE MEMORY
Log trades, research conclusions, lessons learned.

Report findings to user." 2>/dev/null && echo "✓ Trader cron created" || echo "⚠ Trader cron may already exist"

# Position Monitor (every 3h)
clawdbot cron add \
  --name "Polymarket Position Monitor" \
  --schedule "30 */3 * * *" \
  --tz "Europe/London" \
  --isolated \
  --message "Polymarket position check.

## MEMORY FIRST
Read ~/clawd/memory/2026-*.md for entry prices and context.

## CHECK POSITIONS
source ~/polymarket-venv/bin/activate && python3 ~/clawd/skills/polymarket-trader/scripts/account.py

## ANALYZE
- Positions up >15% → consider profit-taking
- Positions down >20% → evaluate stop-loss
- Markets resolving <24h → flag

## UPDATE MEMORY
Log position status, any actions taken.

Only message user if something notable happened." 2>/dev/null && echo "✓ Position Monitor cron created" || echo "⚠ Position Monitor may already exist"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Your crons:"
clawdbot cron list 2>/dev/null | grep -i polymarket || echo "(run 'clawdbot cron list' to verify)"
echo ""
echo "Next steps:"
echo "1. Set POLYMARKET_PRIVATE_KEY in ~/.bashrc"
echo "2. Fund your Polygon wallet with USDC"
echo "3. Say 'Check my Polymarket balance' to test"
