#!/bin/bash
# CDK deployment script for The Alchemiser Quantitative Trading System
#
# Replaces scripts/deploy.sh (SAM-based). Deploys all 7 CDK stacks in
# dependency order using `cdk deploy --all`.
#
# Usage:
#   ./scripts/cdk_deploy.sh dev          # Deploy to dev
#   ./scripts/cdk_deploy.sh staging      # Deploy to staging
#   ./scripts/cdk_deploy.sh prod         # Deploy to prod
#   ./scripts/cdk_deploy.sh dev --diff   # Preview changes (cdk diff)

set -e

# Usage: ./scripts/cdk_deploy.sh [dev|staging|prod] [--diff]
ENVIRONMENT="${1:-prod}"
DIFF_MODE=false

if [ "$2" = "--diff" ]; then
    DIFF_MODE=true
fi

if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "Invalid environment: $ENVIRONMENT (use 'dev', 'staging', or 'prod')" >&2
    exit 1
fi

# Load environment variables: base .env first, then environment-specific overrides.
# .env.dev / .env.staging / .env.prod overlay on top of .env so that the correct
# Alpaca keys (paper vs live) are used per environment.
if [ -f ".env" ]; then
    echo "Loading base environment variables from .env..."
    set -a
    source .env
    set +a
fi

ENV_FILE=".env.${ENVIRONMENT}"
if [ -f "$ENV_FILE" ]; then
    echo "Loading environment overrides from ${ENV_FILE}..."
    set -a
    source "$ENV_FILE"
    set +a
fi

echo ""
echo "Deploying The Alchemiser (CDK)"
echo "================================================"
echo "Environment: $ENVIRONMENT"

# Check we're in the project root
if [ ! -f "cdk.json" ]; then
    echo "Error: cdk.json not found. Run from the project root directory." >&2
    exit 1
fi

# Verify CDK CLI is available
if ! command -v npx &> /dev/null; then
    echo "Error: npx not found. Install Node.js first." >&2
    exit 1
fi

# Validate required credentials
if [ -z "${ALPACA__KEY:-}" ] || [ -z "${ALPACA__SECRET:-}" ]; then
    # Try legacy env var names from .env / CD workflow
    if [ -n "${ALPACA_KEY:-}" ]; then
        export ALPACA__KEY="$ALPACA_KEY"
        export ALPACA__SECRET="$ALPACA_SECRET"
    else
        echo "Error: ALPACA__KEY and ALPACA__SECRET must be set." >&2
        exit 1
    fi
fi

# Bridge legacy ALPACA_ENDPOINT -> ALPACA__ENDPOINT
if [ -z "${ALPACA__ENDPOINT:-}" ] && [ -n "${ALPACA_ENDPOINT:-}" ]; then
    export ALPACA__ENDPOINT="$ALPACA_ENDPOINT"
fi

# Set endpoint defaults per environment
if [ -z "${ALPACA__ENDPOINT:-}" ]; then
    if [ "$ENVIRONMENT" = "prod" ]; then
        export ALPACA__ENDPOINT="https://api.alpaca.markets"
    else
        export ALPACA__ENDPOINT="https://paper-api.alpaca.markets/v2"
    fi
fi

# Set equity deployment pct default
if [ -z "${ALPACA__EQUITY_DEPLOYMENT_PCT:-}" ]; then
    if [ -n "${EQUITY_DEPLOYMENT_PCT:-}" ]; then
        export ALPACA__EQUITY_DEPLOYMENT_PCT="$EQUITY_DEPLOYMENT_PCT"
    else
        export ALPACA__EQUITY_DEPLOYMENT_PCT="1.0"
    fi
fi

# Log level
if [ -z "${ALCHEMISER_LOG_LEVEL:-}" ]; then
    if [ "$ENVIRONMENT" = "prod" ]; then
        export ALCHEMISER_LOG_LEVEL="INFO"
    else
        export ALCHEMISER_LOG_LEVEL="DEBUG"
    fi
fi

# Export STAGE for infra/app.py
export STAGE="$ENVIRONMENT"

echo "  Stage:    $ENVIRONMENT"
echo "  Endpoint: $ALPACA__ENDPOINT"
echo "  Log level: $ALCHEMISER_LOG_LEVEL"

# Safety check: warn if deploying non-prod with live keys
if [ "$ENVIRONMENT" != "prod" ]; then
    if echo "$ALPACA__ENDPOINT" | grep -qv "paper"; then
        echo ""
        echo "  WARNING: Deploying to $ENVIRONMENT with a live (non-paper) endpoint!"
        echo "  Endpoint: $ALPACA__ENDPOINT"
        echo "  Consider creating .env.${ENVIRONMENT} with paper keys."
    fi
    if echo "${ALPACA__KEY:-}" | grep -q "^AK"; then
        echo ""
        echo "  WARNING: ALPACA__KEY starts with 'AK' (live key pattern)."
        echo "  Dev/staging should use paper keys (start with 'PK')."
        echo "  Create .env.${ENVIRONMENT} with paper credentials to fix this."
    fi
fi

echo ""

# Build CDK context args
CDK_CONTEXT="-c stage=$ENVIRONMENT"

if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
    CDK_CONTEXT="$CDK_CONTEXT -c notification_email=$NOTIFICATION_EMAIL"
fi

if [ "$DIFF_MODE" = true ]; then
    echo "Running cdk diff (preview mode)..."
    npx cdk diff --all $CDK_CONTEXT
else
    echo "Deploying all stacks..."
    npx cdk deploy --all \
        $CDK_CONTEXT \
        --require-approval never \
        --rollback \
        --concurrency 3
fi

echo ""
echo "Deployment complete!"
