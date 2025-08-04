#!/bin/bash
# Simple SAM deployment script for The Alchemiser Quantitative Trading System

set -e

echo "🚀 Deploying The Alchemiser Quantitative Trading System with SAM"
echo "================================================"

# Remove any existing requirements.txt from root to avoid duplication
# (dependencies come from the layer in dependencies/requirements.txt)
echo "🧹 Removing root requirements.txt to avoid duplication with layer..."
rm -f requirements.txt

# Ensure dependencies layer has up-to-date requirements
echo "📦 Updating dependencies layer requirements (production only)..."
poetry export --only=main -f requirements.txt --without-hashes -o dependencies/requirements.txt

# Build the SAM application
echo "🔨 Building SAM application..."
sam build

# Deploy the application
echo "🚀 Deploying to AWS..."
sam deploy

echo "✅ Deployment complete!"
echo ""
echo "To test your deployment:"
echo "  sam local invoke TradingSystemFunction"
echo ""
echo "To view logs:"
echo "  sam logs -n TradingSystemFunction --tail"
