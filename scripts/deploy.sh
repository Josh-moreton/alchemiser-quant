#!/bin/bash
# Optimized SAM deployment script for The Alchemiser Quantitative Trading System

set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "📝 Loading environment variables from .env..."
    set -a  # automatically export all variables
    source .env
    set +a
fi

echo "🚀 Deploying The Alchemiser Quantitative Trading System with SAM"
echo "================================================"

# Usage: ./scripts/deploy.sh [dev|prod]
ENVIRONMENT="${1:-prod}"
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo "❌ Invalid environment: $ENVIRONMENT (use 'dev' or 'prod')"
    exit 1
fi
echo "Environment: $ENVIRONMENT"

# Check if we're in the right directory
if [ ! -f "template.yaml" ]; then
    echo "❌ Error: template.yaml not found. Make sure you're in the project root directory."
    exit 1
fi

# Check if sam CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ Error: AWS SAM CLI is not installed. Please install it first:"
    echo "   pip install aws-sam-cli"
    exit 1
fi

# Check if Docker is running (required for --use-container builds)
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker is not running. SAM requires Docker for Lambda-compatible builds."
    echo "   Please start Docker Desktop and try again."
    exit 1
fi

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed. Please install it first."
    exit 1
fi

# Ensure poetry export plugin is available or provide a safe fallback
echo "🔧 Checking Poetry export capability..."
if ! poetry help export > /dev/null 2>&1; then
    echo "⚠️  'poetry export' not found. Attempting to install poetry-plugin-export..."
    # First try via Poetry's plugin system
    if ! poetry self add "poetry-plugin-export>=1.7.1" > /dev/null 2>&1; then
        echo "⚠️  Could not install plugin via 'poetry self add'."
        # If poetry was installed via pipx, try pipx inject as a fallback (best-effort)
        if command -v pipx > /dev/null 2>&1; then
            echo "ℹ️  Trying 'pipx inject poetry poetry-plugin-export'..."
            pipx inject poetry poetry-plugin-export > /dev/null 2>&1 || true
        fi
    fi
fi

# Remove any existing requirements.txt from root to avoid duplication
# (dependencies come from the layer in dependencies/requirements.txt)
echo "🧹 Removing root requirements.txt to avoid duplication with layer..."
rm -f requirements.txt

# Ensure dependencies layer has up-to-date requirements
mkdir -p dependencies
if poetry help export > /dev/null 2>&1; then
    echo "📦 Updating dependencies layer requirements (production only)..."
    poetry export --only=main -f requirements.txt --without-hashes -o dependencies/requirements.txt
    # Strip AWS-managed SDKs to rely on Lambda's built-in boto3/botocore and slim the layer
    if [ -f "dependencies/requirements.txt" ]; then
        sed -i.bak '/^boto3[<=>]/d;/^botocore[<=>]/d' dependencies/requirements.txt && rm -f dependencies/requirements.txt.bak || true
    fi
    # Remove pydantic-core pin if present (allow resolver to pick compatible core)
    sed -i.bak '/^pydantic-core==/d' dependencies/requirements.txt && rm -f dependencies/requirements.txt.bak
else
    if [ -f "dependencies/requirements.txt" ] && [ -s "dependencies/requirements.txt" ]; then
        echo "⚠️  Poetry export unavailable; using existing dependencies/requirements.txt as-is."
    else
        echo "❌ Error: 'poetry export' is unavailable and no existing dependencies/requirements.txt found."
        echo "   Try installing the plugin manually: 'poetry self add poetry-plugin-export'"
        exit 1
    fi
fi

# Check if the dependencies file was created successfully
if [ ! -f "dependencies/requirements.txt" ]; then
    echo "❌ Error: Failed to create dependencies/requirements.txt"
    exit 1
fi

echo "✅ Dependencies exported: $(wc -l < dependencies/requirements.txt) packages"

# Build the SAM application (skip if already built, e.g., by CI/CD)
if [ -f ".aws-sam/build/template.yaml" ]; then
    echo "ℹ️  SAM build artifacts already exist, skipping build..."
    echo "   (To force rebuild, run: rm -rf .aws-sam)"
else
    echo "🔨 Building SAM application..."
    # Use --use-container to build in Lambda-compatible environment
    # Note: CodeUri now points to the_alchemiser/ for cleaner packaging
    sam build --use-container --parallel --config-env "$ENVIRONMENT"
fi

# Show actual built package sizes
echo ""
echo "📦 Built package sizes:"
if [ -d ".aws-sam/build/DependenciesLayer" ]; then
    echo "   Dependencies layer: $(du -sh .aws-sam/build/DependenciesLayer 2>/dev/null | cut -f1 || echo 'N/A')"
fi
if [ -d ".aws-sam/build/TradingSystemFunction" ]; then
    echo "   Function code: $(du -sh .aws-sam/build/TradingSystemFunction 2>/dev/null | cut -f1 || echo 'N/A')"
fi
echo ""

# Deploy the application
echo "🚀 Deploying to AWS..."

if [ "$ENVIRONMENT" = "dev" ]; then
    if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
        echo "❌ ALPACA_KEY and ALPACA_SECRET must be set for dev deploy (env)." >&2
        exit 1
    fi
    ALPACA_ENDPOINT_PARAM=${ALPACA_ENDPOINT:-"https://paper-api.alpaca.markets/v2"}
    EMAIL_PASSWORD_PARAM=${EMAIL__PASSWORD:-""}

    PARAMS=(
        "Stage=dev"
        "AlpacaKey=$ALPACA_KEY"
        "AlpacaSecret=$ALPACA_SECRET"
        "AlpacaEndpoint=$ALPACA_ENDPOINT_PARAM"
        "LoggingLevel=${LOGGING__LEVEL:-INFO}"
        "DslMaxWorkers=${ALCHEMISER_DSL_MAX_WORKERS:-7}"
    )
    if [[ -n "$EMAIL_PASSWORD_PARAM" ]]; then
        PARAMS+=("EmailPassword=$EMAIL_PASSWORD_PARAM")
    fi

    sam deploy \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --config-env "$ENVIRONMENT" \
        --parameter-overrides ${PARAMS[@]}
else
    # Production: use the same ALPACA_* variables, mapped to Prod* parameters
    if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
        echo "❌ ALPACA_KEY and ALPACA_SECRET must be set for prod deploy (env)." >&2
        exit 1
    fi
    PROD_ALPACA_ENDPOINT_PARAM=${ALPACA_ENDPOINT:-"https://api.alpaca.markets"}
    EMAIL_PASSWORD_PARAM=${EMAIL__PASSWORD:-""}

    PARAMS=(
        "Stage=prod"
        "ProdAlpacaKey=$ALPACA_KEY"
        "ProdAlpacaSecret=$ALPACA_SECRET"
        "ProdAlpacaEndpoint=$PROD_ALPACA_ENDPOINT_PARAM"
        "LoggingLevel=${LOGGING__LEVEL:-INFO}"
        "DslMaxWorkers=${ALCHEMISER_DSL_MAX_WORKERS:-7}"
    )
    if [[ -n "$EMAIL_PASSWORD_PARAM" ]]; then
        PARAMS+=("ProdEmailPassword=$EMAIL_PASSWORD_PARAM")
    fi

    sam deploy \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --config-env "$ENVIRONMENT" \
        --parameter-overrides ${PARAMS[@]}
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🧪 To test your deployment:"
echo "   sam local invoke TradingSystemFunction"
echo ""
echo "📊 To view logs:"
echo "   sam logs -n TradingSystemFunction --tail"
echo ""
echo "🔗 To get the Lambda function URL:"
echo "   aws lambda get-function-url-config --function-name TradingSystemFunction"
