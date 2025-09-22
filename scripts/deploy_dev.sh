#!/usr/bin/env bash
set -euo pipefail

# Deploy the dev stack using SAM with environment-provided paper keys
# Required env vars: ALPACA_KEY, ALPACA_SECRET
# Optional: ALPACA_ENDPOINT (defaults to Alpaca paper endpoint)

STACK="the-alchemiser-v2-dev"
REGION="us-east-1"

if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
  echo "ALPACA_KEY and ALPACA_SECRET must be set in the environment" >&2
  exit 1
fi

ALPACA_ENDPOINT_PARAM=${ALPACA_ENDPOINT:-"https://paper-api.alpaca.markets"}

sam build --parallel
sam deploy \
  --config-env dev \
  --stack-name "$STACK" \
  --region "$REGION" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --resolve-s3 \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --parameter-overrides \
    Stage=dev \
    TradeLedgerBucketName=the-alchemiser-v2-s3-dev \
    SecretName=the-alchemiser-v2-secrets-dev \
    AlpacaKey="$ALPACA_KEY" \
    AlpacaSecret="$ALPACA_SECRET" \
    AlpacaEndpoint="$ALPACA_ENDPOINT_PARAM"

echo "Deployed $STACK to $REGION."
