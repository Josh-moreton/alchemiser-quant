#!/usr/bin/env bash
# Test script to manually invoke the Data Lambda for testing data availability
#
# Usage:
#   ./scripts/test_data_refresh.sh              # Refresh all symbols
#   ./scripts/test_data_refresh.sh SPY QQQ      # Refresh specific symbols
#   ./scripts/test_data_refresh.sh --full-seed SPY  # Full seed for specific symbols

set -euo pipefail

STAGE="${1:-dev}"
SYMBOLS=()
FULL_SEED=false

# Parse arguments
shift_count=0
for arg in "$@"; do
    if [[ "$arg" == "--full-seed" ]]; then
        FULL_SEED=true
    elif [[ "$arg" != "dev" && "$arg" != "prod" ]]; then
        SYMBOLS+=("$arg")
    fi
done

# Build payload
if [ ${#SYMBOLS[@]} -eq 0 ]; then
    echo "🔄 Refreshing ALL symbols from strategy configs..."
    PAYLOAD='{"action": "refresh"}'
else
    SYMBOL_JSON=$(printf '%s\n' "${SYMBOLS[@]}" | jq -R . | jq -s .)
    if [ "$FULL_SEED" = true ]; then
        echo "🌱 Full seed for symbols: ${SYMBOLS[*]}"
        PAYLOAD=$(jq -n --argjson symbols "$SYMBOL_JSON" '{action: "refresh", symbols: $symbols, full_seed: true}')
    else
        echo "🔄 Refreshing symbols: ${SYMBOLS[*]}"
        PAYLOAD=$(jq -n --argjson symbols "$SYMBOL_JSON" '{action: "refresh", symbols: $symbols}')
    fi
fi

# Get function name
FUNCTION_NAME="alchemiser-${STAGE}-data"

echo "📡 Invoking Lambda: $FUNCTION_NAME"
echo "📦 Payload: $PAYLOAD"
echo ""

# Invoke Lambda and capture response
RESPONSE=$(aws lambda invoke \
    --function-name "$FUNCTION_NAME" \
    --payload "$PAYLOAD" \
    --cli-binary-format raw-in-base64-out \
    --no-cli-pager \
    /dev/stdout 2>&1)

# Parse and display response
echo ""
echo "📊 Response:"
echo "$RESPONSE" | jq .

# Check status
STATUS_CODE=$(echo "$RESPONSE" | jq -r '.statusCode // 500')
if [ "$STATUS_CODE" -eq 200 ]; then
    echo ""
    echo "✅ Data refresh completed successfully"
elif [ "$STATUS_CODE" -eq 206 ]; then
    echo ""
    echo "⚠️  Partial success - some symbols failed"
    echo "$RESPONSE" | jq -r '.body.failed_symbols[]?' | while read -r symbol; do
        echo "   ❌ $symbol"
    done
else
    echo ""
    echo "❌ Data refresh failed"
    exit 1
fi
