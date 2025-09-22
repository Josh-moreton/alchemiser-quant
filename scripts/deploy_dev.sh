#!/usr/bin/env bash
set -euo pipefail

# Deploy the dev stack using SAM with environment-provided paper keys
# Required env vars: ALPACA_KEY, ALPACA_SECRET
# Optional: ALPACA_ENDPOINT (defaults to Alpaca paper endpoint)

STACK="the-alchemiser-v2-dev"
REGION="us-east-1"
DRY_RUN_FLAG="${DRY_RUN:-0}"

# Try to load ALPACA_* from common dotenv files without sourcing arbitrary content
load_from_file() {
  local f="$1"
  [[ -f "$f" ]] || return 0
  [[ -z "${ALPACA_KEY:-}" ]] && ALPACA_KEY="$(grep -E '^ALPACA_KEY=' "$f" | tail -n1 | sed -E 's/^ALPACA_KEY=(.*)$/\1/')" || true
  [[ -z "${ALPACA_SECRET:-}" ]] && ALPACA_SECRET="$(grep -E '^ALPACA_SECRET=' "$f" | tail -n1 | sed -E 's/^ALPACA_SECRET=(.*)$/\1/')" || true
  [[ -z "${ALPACA_ENDPOINT:-}" ]] && ALPACA_ENDPOINT="$(grep -E '^ALPACA_ENDPOINT=' "$f" | tail -n1 | sed -E 's/^ALPACA_ENDPOINT=(.*)$/\1/')" || true
}

for SECRETS_FILE in scripts/dev.secrets .env.dev .env.local .env; do
  load_from_file "$SECRETS_FILE"
done

# Ensure required env vars are set (avoid unbound variable with -u)
if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
  echo "ALPACA_KEY and ALPACA_SECRET must be set in the environment" >&2
  exit 1
fi

ALPACA_ENDPOINT_PARAM=${ALPACA_ENDPOINT:-"https://paper-api.alpaca.markets/v2"}

sam build --parallel
DEPLOY_ARGS=(
  --config-env dev
  --stack-name "$STACK"
  --region "$REGION"
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM
  --resolve-s3
  --no-confirm-changeset
  --no-fail-on-empty-changeset
  --parameter-overrides
  Stage=dev
  TradeLedgerBucketName=the-alchemiser-v2-s3-dev
  AlpacaKey="$ALPACA_KEY"
  AlpacaSecret="$ALPACA_SECRET"
  AlpacaEndpoint="$ALPACA_ENDPOINT_PARAM"
)

if [[ "$DRY_RUN_FLAG" == "1" ]]; then
  echo "Running in DRY RUN mode (no changes executed)."
  DEPLOY_ARGS+=( --no-execute-changeset )
fi

sam deploy "${DEPLOY_ARGS[@]}"

if [[ "$DRY_RUN_FLAG" == "1" ]]; then
  echo "Created a changeset without executing. Review in CloudFormation console:"
  echo "  https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks"
  echo "Re-run without DRY_RUN=1 to apply."
else
  echo "Deployed $STACK to $REGION."
fi
