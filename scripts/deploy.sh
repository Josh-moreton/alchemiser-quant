#!/bin/bash
# Multi-stack SAM deployment script for The Alchemiser Quantitative Trading System
#
# Cross-stack references use SSM Parameter Store (not CloudFormation Exports)
# to avoid the "Cannot update export as it is in use" constraint when layer
# versions change every deploy.
#
# Migration handling:
#   If this is the first deploy after switching from CF Exports to SSM, the
#   script detects the existing CF exports, bootstraps SSM parameters from
#   current stack outputs, deploys consuming stacks first (to remove their
#   Fn::ImportValue dependencies), then deploys the shared stack (which can
#   now remove its exports freely).
#
# Normal flow: shared -> data -> core
# Migration flow: bootstrap SSM -> build all -> data -> core -> shared -> data -> core

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
# STACK NAME DEFINITIONS
# ============================================================================
SHARED_STACK_NAME="alchemiser-${ENVIRONMENT}-shared"
DATA_STACK_NAME="alchemiser-${ENVIRONMENT}-data"
CORE_STACK_NAME="alchemiser-${ENVIRONMENT}"

# ============================================================================
# SSM MIGRATION: Bootstrap SSM parameters from existing CF Exports
# ============================================================================
# Check if the shared stack still has CF Exports that consumers depend on.
# If so, we need to bootstrap SSM parameters first, then deploy consumers
# to remove their imports before the shared stack can update.
bootstrap_ssm_from_stack_outputs() {
    local stack_name="$1"
    local ssm_prefix="$2"  # e.g. /alchemiser/dev/shared

    echo "   Bootstrapping SSM parameters from $stack_name outputs..."

    # Get all outputs from the stack
    local outputs
    outputs=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --query 'Stacks[0].Outputs' \
        --output json \
        --no-cli-pager 2>/dev/null || echo "[]")

    if [ "$outputs" = "[]" ] || [ "$outputs" = "null" ]; then
        echo "   No outputs found for $stack_name, skipping bootstrap."
        return
    fi

    # Parse each output and write to SSM
    echo "$outputs" | python3 -c "
import json, sys, subprocess
outputs = json.load(sys.stdin)
prefix = '${ssm_prefix}'
for output in outputs:
    key = output['OutputKey']
    value = output['OutputValue']
    param_name = f'{prefix}/{key}'
    # Skip DeploymentStage - not needed in SSM
    if key == 'DeploymentStage':
        continue
    print(f'   Writing SSM: {param_name}')
    subprocess.run([
        'aws', 'ssm', 'put-parameter',
        '--name', param_name,
        '--value', value,
        '--type', 'String',
        '--overwrite',
        '--no-cli-pager'
    ], check=True, capture_output=True)
print(f'   Bootstrapped {len([o for o in outputs if o[\"OutputKey\"] != \"DeploymentStage\"])} SSM parameters.')
"
}

check_exports_exist() {
    local stack_name="$1"
    local export_name="$2"
    aws cloudformation list-exports \
        --query "Exports[?Name=='${export_name}'].Value" \
        --output text \
        --no-cli-pager 2>/dev/null | grep -q .
}

needs_migration() {
    # Check if the shared stack still has CF Exports (the old pattern).
    # If the export exists, consumers may still be importing it.
    check_exports_exist "$SHARED_STACK_NAME" "${SHARED_STACK_NAME}-StrategyLayerArn"
}

# ============================================================================
# BUILD ALL STACKS
# ============================================================================
build_all_stacks() {
    echo ""
    echo "Building shared stack..."
    sam build \
        --template template-shared.yaml \
        --build-dir .aws-sam/build-shared \
        --parallel

    echo ""
    echo "Building data stack..."
    sam build \
        --template template-data.yaml \
        --build-dir .aws-sam/build-data \
        --parallel

    echo ""
    echo "Building core trading stack..."
    sam build --parallel --config-env "$ENVIRONMENT"

    # Show built package sizes
    echo ""
    echo "Built package sizes:"
    if [ -d ".aws-sam/build/StrategyFunction" ]; then
        echo "   Strategy function code: $(du -sh .aws-sam/build/StrategyFunction 2>/dev/null | cut -f1 || echo 'N/A')"
    fi
    echo ""
}

# ============================================================================
# DEPLOY FUNCTIONS
# ============================================================================
deploy_shared() {
    local SHARED_PARAMS=("Stage=$ENVIRONMENT")
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        SHARED_PARAMS+=("NotificationEmail=$NOTIFICATION_EMAIL")
    fi

    echo "Deploying shared stack ($SHARED_STACK_NAME)..."
    sam deploy \
        --template .aws-sam/build-shared/template.yaml \
        --stack-name "$SHARED_STACK_NAME" \
        --region us-east-1 \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --no-confirm-changeset \
        --parameter-overrides ${SHARED_PARAMS[@]}
    echo "Shared infrastructure deployed."
}

deploy_data() {
    local DATA_PARAMS=("Stage=$ENVIRONMENT")
    resolve_alpaca_params "$ENVIRONMENT" DATA_PARAMS

    echo "Deploying data stack ($DATA_STACK_NAME)..."
    sam deploy \
        --template .aws-sam/build-data/template.yaml \
        --stack-name "$DATA_STACK_NAME" \
        --region us-east-1 \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --no-confirm-changeset \
        --parameter-overrides ${DATA_PARAMS[@]}
    echo "Data & Dashboard stack deployed."
}

deploy_core() {
    local CORE_PARAMS=("Stage=$ENVIRONMENT")
    resolve_alpaca_params "$ENVIRONMENT" CORE_PARAMS

    echo "Deploying core trading stack ($CORE_STACK_NAME)..."
    sam deploy \
        --stack-name "$CORE_STACK_NAME" \
        --region us-east-1 \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --no-confirm-changeset \
        --config-env "$ENVIRONMENT" \
        --parameter-overrides ${CORE_PARAMS[@]}
    echo "Core Trading stack deployed."
}

# ============================================================================
# MAIN DEPLOYMENT LOGIC
# ============================================================================

if needs_migration; then
    echo ""
    echo "========================================"
    echo " CF Export -> SSM Migration Detected"
    echo "========================================"
    echo "Shared stack still has CloudFormation Exports."
    echo "Running migration: bootstrap SSM -> data -> core -> shared -> data -> core"
    echo ""

    # Step 1: Bootstrap SSM parameters from current stack outputs
    echo "--- Step 1/6: Bootstrap SSM parameters ---"
    bootstrap_ssm_from_stack_outputs "$SHARED_STACK_NAME" "/alchemiser/${ENVIRONMENT}/shared"
    # Also bootstrap data stack SSM params if it exists
    if aws cloudformation describe-stacks --stack-name "$DATA_STACK_NAME" --no-cli-pager > /dev/null 2>&1; then
        bootstrap_ssm_from_stack_outputs "$DATA_STACK_NAME" "/alchemiser/${ENVIRONMENT}/data"
    fi

    # Step 2: Build all stacks
    echo ""
    echo "--- Step 2/6: Build all stacks ---"
    build_all_stacks

    # Step 3: Deploy consumers first (removes Fn::ImportValue dependencies)
    echo ""
    echo "--- Step 3/6: Deploy data stack (remove imports) ---"
    deploy_data

    echo ""
    echo "--- Step 4/6: Deploy core stack (remove imports) ---"
    deploy_core

    # Step 5: Deploy shared stack (can now remove/update exports freely)
    echo ""
    echo "--- Step 5/6: Deploy shared stack (update exports + SSM) ---"
    deploy_shared

    # Step 6: Redeploy consumers to pick up new layer ARNs from SSM
    echo ""
    echo "--- Step 6/6: Redeploy consumers with new layer ARNs ---"
    deploy_data
    deploy_core

    echo ""
    echo "========================================"
    echo " Migration complete! Future deploys will use normal order."
    echo "========================================"
else
    # Normal deploy order: shared -> data -> core
    echo ""
    echo "========================================"
    echo " Normal Deploy (SSM-based cross-stack refs)"
    echo "========================================"

    build_all_stacks

    echo ""
    echo "========================================"
    echo " STACK 1/3: Shared Infrastructure"
    echo "========================================"
    deploy_shared

    echo ""
    echo "========================================"
    echo " STACK 2/3: Data & Dashboard"
    echo "========================================"
    deploy_data

    echo ""
    echo "========================================"
    echo " STACK 3/3: Core Trading"
    echo "========================================"
    deploy_core
fi

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
