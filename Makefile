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
	@echo "🔧 Installing The Alchemiser with Poetry..."
	poetry install

dev:
	@echo "🔧 Installing The Alchemiser with development dependencies (Poetry groups)..."
	poetry install --with dev

# Trading Commands (using the CLI)
run-signals:
	@echo "🎯 Running signal analysis mode (no trading)..."
	poetry run alchemiser bot

run-trade:
	@echo "💰 Running paper trading..."
	poetry run alchemiser trade

run-trade-live:
	@echo "⚠️  Running LIVE trading (real money)..."
	poetry run alchemiser trade --live

status:
	@echo "📊 Checking account status..."
	poetry run alchemiser status

# Development
test:
        @echo "🧪 Running tests..."
        poetry run pytest tests/ -v

contract-tests:
        @echo "🤝 Running contract tests..."
        poetry run pytest tests/contracts -m contract -v

check-no-legacy-dataprovider:
        @bash tools/ci/check_no_legacy_dataprovider.sh

smoke:
        @echo "🚬 Running CLI smoke tests..."
        poetry run pytest tests/e2e/test_cli_trade.py -v

format:
	@echo "🎨 Formatting code..."
	poetry run black the_alchemiser/ tests/
	poetry run ruff check --fix the_alchemiser/ tests/

lint:
	@echo "🔍 Running linting..."
	poetry run ruff check the_alchemiser/ tests/

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
	poetry run alchemiser deploy


