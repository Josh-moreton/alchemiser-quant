#!/usr/bin/env bash
# CI check to prevent raw json.dumps usage in the_alchemiser/ code
# This ensures all JSON serialization goes through safe_json_dumps or event_to_detail_str

set -e

echo "Checking for raw json.dumps usage..."

# Allowlist: files where json.dumps is acceptable
ALLOWLIST=(
  "the_alchemiser/shared/utils/serialization.py"
  "the_alchemiser/execution_v2/services/trade_ledger.py"
  "the_alchemiser/shared/schemas/strategy_allocation.py"
)

# Find all json.dumps occurrences
violations=()
while IFS= read -r line; do
  file=$(echo "$line" | cut -d: -f1)
  
  # Check if file is in allowlist
  is_allowed=false
  for allowed in "${ALLOWLIST[@]}"; do
    if [[ "$file" == "$allowed" ]]; then
      is_allowed=true
      break
    fi
  done
  
  if [[ "$is_allowed" == false ]]; then
    violations+=("$line")
  fi
done < <(git grep -n 'json\.dumps(' -- 'the_alchemiser/**/*.py' || true)

if [ ${#violations[@]} -gt 0 ]; then
  echo "❌ Found ${#violations[@]} raw json.dumps usage(s) outside allowlist:"
  printf '%s\n' "${violations[@]}"
  echo ""
  echo "Please use one of these instead:"
  echo "  - safe_json_dumps() for general JSON serialization"
  echo "  - event_to_detail_str() for EventBridge event publishing"
  echo "  - model_dump_json() on Pydantic models"
  echo ""
  echo "If this usage is intentional and safe, add the file to ALLOWLIST in scripts/check_json_dumps.sh"
  exit 1
fi

echo "✅ All json.dumps usage is allowlisted"
exit 0
