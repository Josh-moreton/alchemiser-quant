# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help install dev clean run-signals run-trade run-trade-live status deploy format lint importlint

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
	@echo "  format          Format code with Ruff (formatter + fixes)"
	@echo "  lint            Run linting and architectural checks"
	@echo "  importlint      Check architectural boundaries only"
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
format:
	@echo "🎨 Formatting code (Ruff formatter + auto-fix lint)..."
	poetry run ruff format the_alchemiser/
	poetry run ruff check --fix the_alchemiser/

lint:
	@echo "🔍 Running linting..."
	poetry run ruff check the_alchemiser/
	@echo "🏗️ Checking architectural boundaries..."
	poetry run lint-imports

importlint:
	@echo "🏗️ Checking architectural boundaries with import-linter..."
	poetry run lint-imports

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
