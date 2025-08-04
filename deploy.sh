#!/bin/bash
# Simple SAM deployment script for The Alchemiser Quantitative Trading System

set -e

echo "🚀 Deploying The Alchemiser Quantitative Trading System with SAM"
echo "================================================"

# Export Poetry dependencies to requirements.txt
echo "📦 Exporting Poetry dependencies..."
poetry export -f requirements.txt --without-hashes -o requirements.txt

# Build the SAM application
echo "🔨 Building SAM application..."
sam build

# Deploy the application
echo "🚀 Deploying to AWS..."
sam deploy --guided

echo "✅ Deployment complete!"
echo ""
echo "To test your deployment:"
echo "  sam local invoke TradingSystemFunction"
echo ""
echo "To view logs:"
echo "  sam logs -n TradingSystemFunction --tail"
