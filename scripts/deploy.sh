#!/bin/bash
# Optimized SAM deployment script for The Alchemiser Quantitative Trading System

set -e

echo "🚀 Deploying The Alchemiser Quantitative Trading System with SAM"
echo "================================================"

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
sam build --parallel

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
sam deploy --no-fail-on-empty-changeset

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
