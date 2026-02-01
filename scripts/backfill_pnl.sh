#!/bin/bash
# Backfill daily P&L data for the last 3 months
# Usage: ./scripts/backfill_pnl.sh [dev|staging|prod]

set -e

STAGE="${1:-dev}"
FUNCTION_NAME="alchemiser-${STAGE}-pnl-capture"

echo "🔄 Backfilling P&L data for ${FUNCTION_NAME}"
echo "   Last 3 months of trading days"
echo ""

# Calculate date range (90 days back)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    START_DATE=$(date -v-90d +%Y-%m-%d)
    END_DATE=$(date -v-1d +%Y-%m-%d)
else
    # Linux
    START_DATE=$(date -d "90 days ago" +%Y-%m-%d)
    END_DATE=$(date -d "yesterday" +%Y-%m-%d)
fi

echo "📅 Date range: ${START_DATE} to ${END_DATE}"
echo ""

# Generate list of dates (weekdays only - skip weekends)
CURRENT="$START_DATE"
SUCCESS=0
FAILED=0
SKIPPED=0

while [[ "$CURRENT" < "$END_DATE" ]] || [[ "$CURRENT" == "$END_DATE" ]]; do
    # Get day of week (1=Mon, 7=Sun on macOS; 1=Mon, 0=Sun on Linux)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        DOW=$(date -j -f "%Y-%m-%d" "$CURRENT" +%u 2>/dev/null)
    else
        DOW=$(date -d "$CURRENT" +%u)
    fi
    
    # Skip weekends (Sat=6, Sun=7)
    if [[ "$DOW" -ge 6 ]]; then
        ((SKIPPED++))
    else
        echo -n "📊 Capturing ${CURRENT}... "
        
        RESPONSE=$(aws lambda invoke \
            --function-name "$FUNCTION_NAME" \
            --payload "{\"target_date\": \"${CURRENT}\"}" \
            --cli-binary-format raw-in-base64-out \
            --no-cli-pager \
            /tmp/pnl_response.json 2>&1)
        
        if [[ $? -eq 0 ]]; then
            STATUS=$(cat /tmp/pnl_response.json | python3 -c "import sys,json; print(json.load(sys.stdin).get('body',{}).get('status','unknown'))" 2>/dev/null || echo "unknown")
            if [[ "$STATUS" == "success" ]]; then
                echo "✅"
                ((SUCCESS++))
            else
                echo "⚠️  ($STATUS)"
                ((FAILED++))
            fi
        else
            echo "❌ (invoke failed)"
            ((FAILED++))
        fi
        
        # Rate limit - avoid throttling
        sleep 0.5
    fi
    
    # Increment date
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CURRENT=$(date -j -v+1d -f "%Y-%m-%d" "$CURRENT" +%Y-%m-%d)
    else
        CURRENT=$(date -d "$CURRENT + 1 day" +%Y-%m-%d)
    fi
done

echo ""
echo "════════════════════════════════════════"
echo "✅ Success: ${SUCCESS}"
echo "❌ Failed:  ${FAILED}"
echo "⏭️  Skipped (weekends): ${SKIPPED}"
echo "════════════════════════════════════════"

rm -f /tmp/pnl_response.json
