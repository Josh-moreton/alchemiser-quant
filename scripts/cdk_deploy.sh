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

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    set -a
    source .env
    set +a
fi

echo "Deploying The Alchemiser (CDK)"
echo "================================================"

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
    # Try legacy env var names from CD workflow
    if [ -n "${ALPACA_KEY:-}" ]; then
        export ALPACA__KEY="$ALPACA_KEY"
        export ALPACA__SECRET="$ALPACA_SECRET"
    else
        echo "Error: ALPACA__KEY and ALPACA__SECRET must be set." >&2
        exit 1
    fi
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
