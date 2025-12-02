#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Load environment if .env exists (only simple KEY=VALUE lines)
if [[ -f .env ]]; then
    set -a
    # Filter only valid KEY=VALUE lines (no spaces around =, no complex values)
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        # Only process simple KEY=VALUE lines (no spaces, quotes, or complex structures)
        if [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*=.*$ ]]; then
            # Extract key and value
            key="${line%%=*}"
            value="${line#*=}"
            # Export the variable (handle quoted values)
            value="${value%\"}"
            value="${value#\"}"
            export "$key=$value"
        fi
    done < .env
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

# Ensure poetry export plugin is available
echo "🔧 Checking Poetry export capability..."
if ! poetry help export > /dev/null 2>&1; then
    echo "⚠️  'poetry export' not found. Attempting to install poetry-plugin-export..."
    if ! poetry self add "poetry-plugin-export>=1.7.1" > /dev/null 2>&1; then
        echo "⚠️  Could not install plugin via 'poetry self add'."
        if command -v pipx > /dev/null 2>&1; then
            echo "ℹ️  Trying 'pipx inject poetry poetry-plugin-export'..."
            pipx inject poetry poetry-plugin-export > /dev/null 2>&1 || true
        fi
    fi
fi

# Export dependencies
mkdir -p dependencies
if poetry help export > /dev/null 2>&1; then
    echo "📦 Updating dependencies layer requirements (production only)..."
    poetry export --only=main -f requirements.txt --without-hashes -o dependencies/requirements.txt
    # Strip AWS-managed SDKs to rely on Lambda's built-in boto3/botocore
    if [ -f "dependencies/requirements.txt" ]; then
        sed -i.bak '/^boto3[<=>]/d;/^botocore[<=>]/d' dependencies/requirements.txt && rm -f dependencies/requirements.txt.bak || true
    fi
    # Remove pydantic-core pin if present
    sed -i.bak '/^pydantic-core==/d' dependencies/requirements.txt && rm -f dependencies/requirements.txt.bak || true
else
    if [ -f "dependencies/requirements.txt" ] && [ -s "dependencies/requirements.txt" ]; then
        echo "⚠️  Poetry export unavailable; using existing dependencies/requirements.txt as-is."
    else
        echo "❌ Error: 'poetry export' is unavailable and no existing dependencies/requirements.txt found."
        echo "   Try installing the plugin manually: 'poetry self add poetry-plugin-export'"
        exit 1
    fi
fi

# Verify dependencies file exists
if [ ! -f "dependencies/requirements.txt" ]; then
    echo "❌ Error: Failed to create dependencies/requirements.txt"
    exit 1
fi

echo "✅ Dependencies exported: $(wc -l < dependencies/requirements.txt) packages"

# SAM build
if [ -f ".aws-sam/build/template.yaml" ]; then
    echo "ℹ️  SAM build artifacts already exist, skipping build..."
    echo "   (To force rebuild, run: rm -rf .aws-sam)"
else
    echo "🔨 Building SAM application..."
    sam build --use-container --parallel --config-env "$ENVIRONMENT"
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
