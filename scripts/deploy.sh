#!/bin/bash
# Multi-stack SAM deployment script for The Alchemiser Quantitative Trading System
# Deploys stacks sequentially: shared -> data -> core

set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    set -a  # automatically export all variables
    source .env
    set +a
fi

echo "Deploying The Alchemiser Quantitative Trading System (multi-stack)"
echo "================================================"

# Usage: ./scripts/deploy.sh [dev|staging|prod]
ENVIRONMENT="${1:-prod}"
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "ERROR: Invalid environment: $ENVIRONMENT (use 'dev', 'staging', or 'prod')"
    exit 1
fi
echo "Environment: $ENVIRONMENT"

# Check if we're in the right directory
if [ ! -f "template.yaml" ]; then
    echo "ERROR: template.yaml not found. Make sure you're in the project root directory."
    exit 1
fi

# Check if sam CLI is installed
if ! command -v sam &> /dev/null; then
    echo "ERROR: AWS SAM CLI is not installed. Please install it first:"
    echo "   pip install aws-sam-cli"
    exit 1
fi

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "ERROR: Poetry is not installed. Please install it first."
    exit 1
fi

# Ensure poetry export plugin is available or provide a safe fallback
echo "Checking Poetry export capability..."
if ! poetry help export > /dev/null 2>&1; then
    echo "WARNING: 'poetry export' not found. Attempting to install poetry-plugin-export..."
    if ! poetry self add "poetry-plugin-export>=1.7.1" > /dev/null 2>&1; then
        echo "WARNING: Could not install plugin via 'poetry self add'."
        if command -v pipx > /dev/null 2>&1; then
            echo "INFO: Trying 'pipx inject poetry poetry-plugin-export'..."
            pipx inject poetry poetry-plugin-export > /dev/null 2>&1 || true
        fi
    fi
fi

# Remove any existing requirements.txt from root to avoid duplication
echo "Removing root requirements.txt to avoid duplication with layer..."
rm -f requirements.txt

# Function-specific layers are defined in layers/<function>/requirements.txt
echo "Verifying function-specific layer requirements..."

LAYER_DIRS=("strategy" "portfolio" "execution" "notifications" "data")
for layer in "${LAYER_DIRS[@]}"; do
    if [ ! -f "layers/$layer/requirements.txt" ]; then
        echo "ERROR: layers/$layer/requirements.txt not found"
        exit 1
    fi
    echo "   layers/$layer/requirements.txt: $(wc -l < layers/$layer/requirements.txt | tr -d ' ') lines"
done

echo "All function-specific layer requirements verified"

# ============================================================================
# RESOLVE ALPACA CREDENTIALS PER ENVIRONMENT
# ============================================================================
resolve_alpaca_params() {
    local env="$1"
    local -n params_ref="$2"

    if [ "$env" = "dev" ]; then
        if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
            echo "ERROR: ALPACA_KEY and ALPACA_SECRET must be set for dev deploy (env)." >&2
            exit 1
        fi
        params_ref+=("AlpacaKey=$ALPACA_KEY")
        params_ref+=("AlpacaSecret=$ALPACA_SECRET")
        params_ref+=("AlpacaEndpoint=${ALPACA_ENDPOINT:-https://paper-api.alpaca.markets/v2}")
        params_ref+=("EquityDeploymentPct=${EQUITY_DEPLOYMENT_PCT:-1.0}")
    elif [ "$env" = "staging" ]; then
        if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
            echo "ERROR: ALPACA_KEY and ALPACA_SECRET must be set for staging deploy (env)." >&2
            exit 1
        fi
        params_ref+=("StagingAlpacaKey=$ALPACA_KEY")
        params_ref+=("StagingAlpacaSecret=$ALPACA_SECRET")
        params_ref+=("StagingAlpacaEndpoint=${ALPACA_ENDPOINT:-https://paper-api.alpaca.markets/v2}")
        params_ref+=("StagingEquityDeploymentPct=${EQUITY_DEPLOYMENT_PCT:-1.0}")
    else
        if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
            echo "ERROR: ALPACA_KEY and ALPACA_SECRET must be set for prod deploy (env)." >&2
            exit 1
        fi
        params_ref+=("ProdAlpacaKey=$ALPACA_KEY")
        params_ref+=("ProdAlpacaSecret=$ALPACA_SECRET")
        params_ref+=("ProdAlpacaEndpoint=${ALPACA_ENDPOINT:-https://api.alpaca.markets}")
        params_ref+=("ProdEquityDeploymentPct=${EQUITY_DEPLOYMENT_PCT:-1.0}")
    fi

    # Common optional params
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        params_ref+=("NotificationEmail=$NOTIFICATION_EMAIL")
    fi
}

# ============================================================================
# STACK 1: SHARED INFRASTRUCTURE (template-shared.yaml)
# ============================================================================
echo ""
echo "========================================"
echo " STACK 1/3: Shared Infrastructure"
echo "========================================"

SHARED_CONFIG_ENV="shared-${ENVIRONMENT}"
SHARED_PARAMS=("Stage=$ENVIRONMENT")

# Add notification email for DLQ alerts
if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
    SHARED_PARAMS+=("NotificationEmail=$NOTIFICATION_EMAIL")
fi

echo "Building shared stack..."
sam build \
    --template template-shared.yaml \
    --build-dir .aws-sam/build-shared \
    --parallel \
    --config-env "$SHARED_CONFIG_ENV"

echo "Deploying shared stack..."
sam deploy \
    --template .aws-sam/build-shared/template.yaml \
    --no-fail-on-empty-changeset \
    --resolve-s3 \
    --config-env "$SHARED_CONFIG_ENV" \
    --parameter-overrides ${SHARED_PARAMS[@]}

echo "Shared infrastructure deployed."

# ============================================================================
# STACK 2: DATA & DASHBOARD (template-data.yaml)
# ============================================================================
echo ""
echo "========================================"
echo " STACK 2/3: Data & Dashboard"
echo "========================================"

DATA_CONFIG_ENV="data-${ENVIRONMENT}"
DATA_PARAMS=(
    "Stage=$ENVIRONMENT"
    "SharedStackName=alchemiser-${ENVIRONMENT}-shared"
)

# Add Alpaca credentials (Data Lambda needs them for market data fetching)
resolve_alpaca_params "$ENVIRONMENT" DATA_PARAMS

echo "Building data stack..."
sam build \
    --template template-data.yaml \
    --build-dir .aws-sam/build-data \
    --parallel \
    --config-env "$DATA_CONFIG_ENV"

echo "Deploying data stack..."
sam deploy \
    --template .aws-sam/build-data/template.yaml \
    --no-fail-on-empty-changeset \
    --resolve-s3 \
    --config-env "$DATA_CONFIG_ENV" \
    --parameter-overrides ${DATA_PARAMS[@]}

echo "Data & Dashboard stack deployed."

# ============================================================================
# STACK 3: CORE TRADING (template.yaml)
# ============================================================================
echo ""
echo "========================================"
echo " STACK 3/3: Core Trading"
echo "========================================"

CORE_PARAMS=(
    "Stage=$ENVIRONMENT"
    "SharedStackName=alchemiser-${ENVIRONMENT}-shared"
    "DataStackName=alchemiser-${ENVIRONMENT}-data"
)

# Add Alpaca credentials (needed by Strategy, Portfolio, Execution, etc.)
resolve_alpaca_params "$ENVIRONMENT" CORE_PARAMS

echo "Building core trading stack..."
sam build --parallel --config-env "$ENVIRONMENT"

# Show built package sizes
echo ""
echo "Built package sizes:"
if [ -d ".aws-sam/build/StrategyFunction" ]; then
    echo "   Strategy function code: $(du -sh .aws-sam/build/StrategyFunction 2>/dev/null | cut -f1 || echo 'N/A')"
fi
echo ""

echo "Deploying core trading stack..."
sam deploy \
    --no-fail-on-empty-changeset \
    --resolve-s3 \
    --config-env "$ENVIRONMENT" \
    --parameter-overrides ${CORE_PARAMS[@]}

echo "Core Trading stack deployed."

# ============================================================================
# COMPLETE
# ============================================================================
echo ""
echo "========================================"
echo " All 3 stacks deployed successfully!"
echo "========================================"
echo ""
echo "Stacks deployed:"
echo "   1. alchemiser-${ENVIRONMENT}-shared  (EventBus, Layers, TradeLedger, S3)"
echo "   2. alchemiser-${ENVIRONMENT}-data    (Data Lambda, AccountData Lambda)"
echo "   3. alchemiser-${ENVIRONMENT}         (Strategy, Portfolio, Execution, etc.)"
echo ""
echo "To view logs:"
echo "   sam logs -n StrategyFunction --stack-name alchemiser-${ENVIRONMENT} --tail"
