#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment if .env exists
if [[ -f .env ]]; then
    set -a
    source .env
    set +a
fi

# Validate environment parameter
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <environment>"
    echo "  environment: dev or prod"
    exit 1
fi

ENVIRONMENT=$1

# Validate environment
if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
    echo "Error: Environment must be 'dev' or 'prod'"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Deploying Alchemiser Microservices to $ENVIRONMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Export dependencies
echo "📦 Exporting dependencies..."
poetry export --only=main --without-hashes --output dependencies/requirements.txt

# Strip AWS-managed packages
sed -i.bak '/^boto3==/d; /^botocore==/d' dependencies/requirements.txt
sed -i.bak 's/pydantic-core==.*/pydantic-core/g' dependencies/requirements.txt
rm dependencies/requirements.txt.bak

# SAM build
echo "🔨 Building SAM application..."
if [[ ! -d .aws-sam/build ]]; then
    sam build --use-container --parallel --config-env "$ENVIRONMENT"
else
    echo "Skipping build (artifacts exist)"
fi

# Prepare parameters
declare -a PARAMS=(
    "EnableMicroservices=true"
    "LoggingLevel=${LOGGING__LEVEL:-INFO}"
    "DslMaxWorkers=${ALCHEMISER_DSL_MAX_WORKERS:-7}"
)

# Environment-specific credentials
if [[ "$ENVIRONMENT" == "dev" ]]; then
    if [[ -z "${MICROSERVICES_ALPACA_KEY:-}" || -z "${MICROSERVICES_ALPACA_SECRET:-}" ]]; then
        echo "Error: MICROSERVICES_ALPACA_KEY and MICROSERVICES_ALPACA_SECRET required for microservices"
        exit 1
    fi

    PARAMS+=(
        "MicroservicesAlpacaKey=$MICROSERVICES_ALPACA_KEY"
        "MicroservicesAlpacaSecret=$MICROSERVICES_ALPACA_SECRET"
        "MicroservicesAlpacaEndpoint=${MICROSERVICES_ALPACA_ENDPOINT:-https://paper-api.alpaca.markets/v2}"
        "EmailPassword=${EMAIL__PASSWORD:-}"
    )
elif [[ "$ENVIRONMENT" == "prod" ]]; then
    if [[ -z "${PROD_MICROSERVICES_ALPACA_KEY:-}" || -z "${PROD_MICROSERVICES_ALPACA_SECRET:-}" ]]; then
        echo "Error: PROD_MICROSERVICES_ALPACA_KEY and PROD_MICROSERVICES_ALPACA_SECRET required"
        exit 1
    fi

    PARAMS+=(
        "MicroservicesAlpacaKey=$PROD_MICROSERVICES_ALPACA_KEY"
        "MicroservicesAlpacaSecret=$PROD_MICROSERVICES_ALPACA_SECRET"
        "MicroservicesAlpacaEndpoint=${PROD_MICROSERVICES_ALPACA_ENDPOINT:-https://api.alpaca.markets}"
        "EmailPassword=${PROD_EMAIL__PASSWORD:-}"
    )
fi

# Deploy
echo "🚀 Deploying to $ENVIRONMENT..."
sam deploy \
    --no-fail-on-empty-changeset \
    --resolve-s3 \
    --config-env "microservices-$ENVIRONMENT" \
    --parameter-overrides "${PARAMS[@]}"

echo "✅ Deployment complete!"
echo ""
echo "Function URLs:"
sam list endpoints --config-env "microservices-$ENVIRONMENT" 2>/dev/null || true
