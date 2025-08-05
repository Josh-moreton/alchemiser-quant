# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help install dev test clean run-signals run-trade run-trade-live status deploy format lint

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install         Install package in development mode"
	@echo "  dev             Install with development dependencies"
	@echo ""
	@echo "Trading Commands:"
	@echo "  run-signals     Show strategy signals (no trading)"
	@echo "  run-trade       Execute paper trading"
	@echo "  run-trade-live  Execute LIVE trading (⚠️ real money)"
	@echo "  status          Show account status"
	@echo ""
	@echo "Development:"
	@echo "  test            Run tests"
	@echo "  format          Format code with black"
	@echo "  lint            Run linting"
	@echo "  clean           Clean build artifacts"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy          Deploy to AWS Lambda"

# Setup & Installation
install:
	@echo "🔧 Installing The Alchemiser in development mode..."
	pip install -e .

dev:
	@echo "🔧 Installing The Alchemiser with development dependencies..."
	pip install -e ".[dev]"

# Trading Commands (using the CLI)
run-signals:
	@echo "🎯 Running signal analysis mode (no trading)..."
	alchemiser bot

run-trade:
	@echo "💰 Running paper trading..."
	alchemiser trade

run-trade-live:
	@echo "⚠️  Running LIVE trading (real money)..."
	alchemiser trade --live

status:
	@echo "📊 Checking account status..."
	alchemiser status

# Development
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v

format:
	@echo "🎨 Formatting code..."
	black the_alchemiser/ tests/

lint:
	@echo "🔍 Running linting..."
	ruff check the_alchemiser/ tests/

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Deployment
deploy:
	@echo "🚀 Deploying to AWS Lambda..."
	alchemiser deploy

# Legacy commands (for backward compatibility)
bot: run-bot
trade: run-trade
trade-live: run-trade-live
