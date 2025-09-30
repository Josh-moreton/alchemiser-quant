#!/bin/bash
# Optimized SAM deployment script for The Alchemiser Quantitative Trading System

set -e

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

# Build the SAM application
echo "🔨 Building SAM application..."
sam build --parallel --config-env "$ENVIRONMENT"

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
    # Load Alpaca creds and strategy configs from common dotenv files (best-effort)
    load_from_file() {
        local f="$1"
        [[ -f "$f" ]] || return 0
        [[ -z "${ALPACA_KEY:-}" ]] && ALPACA_KEY="$(grep -E '^ALPACA_KEY=' "$f" | tail -n1 | sed -E 's/^ALPACA_KEY=(.*)$/\1/')" || true
        [[ -z "${ALPACA_SECRET:-}" ]] && ALPACA_SECRET="$(grep -E '^ALPACA_SECRET=' "$f" | tail -n1 | sed -E 's/^ALPACA_SECRET=(.*)$/\1/')" || true
        [[ -z "${ALPACA_ENDPOINT:-}" ]] && ALPACA_ENDPOINT="$(grep -E '^ALPACA_ENDPOINT=' "$f" | tail -n1 | sed -E 's/^ALPACA_ENDPOINT=(.*)$/\1/')" || true
        [[ -z "${STRATEGY_DSL_FILES:-}" ]] && STRATEGY_DSL_FILES="$(grep -E '^STRATEGY__DSL_FILES=' "$f" | tail -n1 | sed -E 's/^STRATEGY__DSL_FILES=(.*)$/\1/')" || true
        [[ -z "${STRATEGY_DSL_ALLOCATIONS:-}" ]] && STRATEGY_DSL_ALLOCATIONS="$(grep -E '^STRATEGY__DSL_ALLOCATIONS=' "$f" | tail -n1 | sed -E 's/^STRATEGY__DSL_ALLOCATIONS=(.*)$/\1/')" || true
    }
    for SECRETS_FILE in scripts/dev.secrets .env.dev .env.local .env; do
        load_from_file "$SECRETS_FILE"
    done

    if [[ -z "${ALPACA_KEY:-}" || -z "${ALPACA_SECRET:-}" ]]; then
        echo "❌ ALPACA_KEY and ALPACA_SECRET must be set for dev deploy (env or .env)." >&2
        exit 1
    fi
    ALPACA_ENDPOINT_PARAM=${ALPACA_ENDPOINT:-"https://paper-api.alpaca.markets/v2"}

    # Set defaults for strategy configs if not found in .env
    STRATEGY_DSL_FILES_PARAM=${STRATEGY_DSL_FILES:-'["1-KMLM.clj","2-Nuclear.clj","3-Starburst.clj","4-What.clj","5-Coin.clj","6-TQQQ-FLT.clj","7-Phoenix.clj"]'}
    STRATEGY_DSL_ALLOCATIONS_PARAM=${STRATEGY_DSL_ALLOCATIONS:-'{"1-KMLM.clj":0.2,"2-Nuclear.clj":0.15,"3-Starburst.clj":0.15,"4-What.clj":0.1,"5-Coin.clj":0.1,"6-TQQQ-FLT.clj":0.15,"7-Phoenix.clj":0.15}'}

    sam deploy \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --config-env "$ENVIRONMENT" \
        --parameter-overrides \
            Stage=dev \
            TradeLedgerBucketName=the-alchemiser-v2-s3-dev \
            AlpacaKey="$ALPACA_KEY" \
            AlpacaSecret="$ALPACA_SECRET" \
            AlpacaEndpoint="$ALPACA_ENDPOINT_PARAM" \
            DevStrategyFiles="$STRATEGY_DSL_FILES_PARAM" \
            DevStrategyAllocations="$STRATEGY_DSL_ALLOCATIONS_PARAM"
else
    # Production deployment - load LIVE_* credentials from .env file
    echo "📋 Loading production credentials from .env file..."

    # Load LIVE_* variables from .env file
    load_live_from_file() {
        local f="$1"
        [[ -f "$f" ]] || return 0
        [[ -z "${LIVE_ALPACA_KEY:-}" ]] && LIVE_ALPACA_KEY="$(grep -E '^LIVE_ALPACA_KEY=' "$f" | tail -n1 | sed -E 's/^LIVE_ALPACA_KEY=(.*)$/\1/')" || true
        [[ -z "${LIVE_ALPACA_SECRET:-}" ]] && LIVE_ALPACA_SECRET="$(grep -E '^LIVE_ALPACA_SECRET=' "$f" | tail -n1 | sed -E 's/^LIVE_ALPACA_SECRET=(.*)$/\1/')" || true
        [[ -z "${LIVE_ALPACA_ENDPOINT:-}" ]] && LIVE_ALPACA_ENDPOINT="$(grep -E '^LIVE_ALPACA_ENDPOINT=' "$f" | tail -n1 | sed -E 's/^LIVE_ALPACA_ENDPOINT=(.*)$/\1/')" || true
        [[ -z "${LIVE_STRATEGY_DSL_FILES:-}" ]] && LIVE_STRATEGY_DSL_FILES="$(grep -E '^LIVE_STRATEGY__DSL_FILES=' "$f" | tail -n1 | sed -E 's/^LIVE_STRATEGY__DSL_FILES=(.*)$/\1/')" || true
        [[ -z "${LIVE_STRATEGY_DSL_ALLOCATIONS:-}" ]] && LIVE_STRATEGY_DSL_ALLOCATIONS="$(grep -E '^LIVE_STRATEGY__DSL_ALLOCATIONS=' "$f" | tail -n1 | sed -E 's/^LIVE_STRATEGY__DSL_ALLOCATIONS=(.*)$/\1/')" || true
        [[ -z "${EMAIL_PASSWORD:-}" ]] && EMAIL_PASSWORD="$(grep -E '^EMAIL__PASSWORD=' "$f" | tail -n1 | sed -E 's/^EMAIL__PASSWORD=(.*)$/\1/')" || true
        [[ -z "${TWELVEDATA_KEY:-}" ]] && TWELVEDATA_KEY="$(grep -E '^TWELVEDATA_KEY=' "$f" | tail -n1 | sed -E 's/^TWELVEDATA_KEY=(.*)$/\1/')" || true
    }

    for SECRETS_FILE in .env; do
        load_live_from_file "$SECRETS_FILE"
    done

    # Check required production credentials
    if [[ -z "${LIVE_ALPACA_KEY:-}" || -z "${LIVE_ALPACA_SECRET:-}" ]]; then
        echo "❌ Error: LIVE_ALPACA_KEY and LIVE_ALPACA_SECRET must be set in .env file for production deployment." >&2
        echo "   Please add them to your .env file with the LIVE_ prefix." >&2
        exit 1
    fi

    # Set defaults for optional parameters
    LIVE_ALPACA_ENDPOINT_PARAM=${LIVE_ALPACA_ENDPOINT:-"https://api.alpaca.markets"}
    EMAIL_PASSWORD_PARAM=${EMAIL_PASSWORD:-""}
    TWELVEDATA_KEY_PARAM=${TWELVEDATA_KEY:-""}

    # Set defaults for strategy configs if not found in .env
    LIVE_STRATEGY_DSL_FILES_PARAM=${LIVE_STRATEGY_DSL_FILES:-'["1-KMLM.clj","2-Nuclear.clj","5-Coin.clj","6-TQQQ-FLT.clj"]'}
    LIVE_STRATEGY_DSL_ALLOCATIONS_PARAM=${LIVE_STRATEGY_DSL_ALLOCATIONS:-'{"1-KMLM.clj":0.4,"2-Nuclear.clj":0.25,"5-Coin.clj":0.1,"6-TQQQ-FLT.clj":0.25}'}

    echo "✅ Production credentials loaded from .env"
    echo "⚠️  WARNING: Using LIVE trading keys - real money will be traded!"
    echo ""

    sam deploy \
        --no-fail-on-empty-changeset \
        --resolve-s3 \
        --config-env "$ENVIRONMENT" \
        --parameter-overrides \
            Stage=prod \
            TradeLedgerBucketName=the-alchemiser-v2-s3 \
            ProdAlpacaKey="$LIVE_ALPACA_KEY" \
            ProdAlpacaSecret="$LIVE_ALPACA_SECRET" \
            ProdAlpacaEndpoint="$LIVE_ALPACA_ENDPOINT_PARAM" \
            ProdEmailPassword="$EMAIL_PASSWORD_PARAM" \
            ProdTwelveDataKey="$TWELVEDATA_KEY_PARAM" \
            ProdStrategyFiles="$LIVE_STRATEGY_DSL_FILES_PARAM" \
            ProdStrategyAllocations="$LIVE_STRATEGY_DSL_ALLOCATIONS_PARAM"
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
