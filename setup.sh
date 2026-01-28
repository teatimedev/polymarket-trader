#!/bin/bash
# Polymarket Trader Skill - Auto Setup
# Run this or ask Moltbot: "Set up Polymarket trading"

set -e

echo "[DICE] Setting up Polymarket Trader skill..."

# Detect shell config file
if [ -n "$ZSH_VERSION" ] || [ "$SHELL" = "/bin/zsh" ] || [ "$SHELL" = "/usr/bin/zsh" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ] || [ "$SHELL" = "/bin/bash" ] || [ "$SHELL" = "/usr/bin/bash" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    # Default to .profile for other shells
    SHELL_CONFIG="$HOME/.profile"
fi

echo "Detected shell config: $SHELL_CONFIG"

# Check for Python venv (cross-platform)
if [ -d "$HOME/polymarket-venv" ]; then
    echo "[OK] Python venv exists"
else
    echo "[PKG] Creating Python virtual environment..."
    python3 -m venv ~/polymarket-venv
    
    # Activate (cross-platform)
    if [ -f "$HOME/polymarket-venv/bin/activate" ]; then
        source ~/polymarket-venv/bin/activate
    elif [ -f "$HOME/polymarket-venv/Scripts/activate" ]; then
        source ~/polymarket-venv/Scripts/activate
    fi
    
    pip install py-clob-client eth-account requests
fi

# Check for credentials
MISSING_CREDS=0

if [ -z "$POLYMARKET_PRIVATE_KEY" ]; then
    echo ""
    echo "[WARN] POLYMARKET_PRIVATE_KEY not set!"
    echo "Add to $SHELL_CONFIG:"
    echo '  export POLYMARKET_PRIVATE_KEY="0x..."'
    MISSING_CREDS=1
fi

if [ -z "$EXA_API_KEY" ]; then
    echo ""
    echo "[WARN] EXA_API_KEY not set!"
    echo "Get your key: https://dashboard.exa.ai/api-keys"
    echo "Add to $SHELL_CONFIG:"
    echo '  export EXA_API_KEY="..."'
    MISSING_CREDS=1
fi

if [ $MISSING_CREDS -eq 1 ]; then
    echo ""
    echo "After adding keys, run: source $SHELL_CONFIG"
    echo ""
fi

# Create config directory for state
mkdir -p "$HOME/.config/polymarket-trader"

# Create cron jobs via Moltbot
echo "[CAL] Setting up cron jobs..."

# Daily Scan (9am)
moltbot cron add \
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

Keep it punchy." 2>/dev/null && echo "[OK] Daily Scan cron created" || echo "[WARN] Daily Scan may already exist"

# Trading Scan (every 6h)
moltbot cron add \
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

Report findings to user." 2>/dev/null && echo "[OK] Trader cron created" || echo "[WARN] Trader cron may already exist"

# Position Monitor (every 3h)
moltbot cron add \
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
- Positions up >15% -> consider profit-taking
- Positions down >20% -> evaluate stop-loss
- Markets resolving <24h -> flag

## UPDATE MEMORY
Log position status, any actions taken.

Only message user if something notable happened." 2>/dev/null && echo "[OK] Position Monitor cron created" || echo "[WARN] Position Monitor may already exist"

echo ""
echo "[OK] Setup complete!"
echo ""
echo "Your crons:"
moltbot cron list 2>/dev/null | grep -i polymarket || echo "(run 'moltbot cron list' to verify)"
echo ""
echo "Next steps:"
echo "1. Set POLYMARKET_PRIVATE_KEY in $SHELL_CONFIG"
echo "2. Fund your Polygon wallet with USDC"
echo "3. Say 'Check my Polymarket balance' to test"
