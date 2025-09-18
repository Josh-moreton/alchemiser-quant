# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help install dev clean run-trade status deploy format lint type-check import-check migration-check typing-audit

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install         Install package in development mode"
	@echo "  dev             Install with development dependencies"
	@echo ""
	@echo "Trading Commands:"
	@echo "  run-trade       Execute trading (includes signal analysis)"
	@echo "  status          Show account status"
	@echo ""
	@echo "Development:"
	@echo "  format          Format code with Ruff (formatter + fixes)"
	@echo "  lint            Run linting"
	@echo "  type-check      Run MyPy type checking"
	@echo "  typing-audit    Run typing architecture audit"
	@echo "  import-check    Check module dependency rules"
	@echo "  migration-check Full migration validation suite"
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
# run-signals command removed - signal analysis is now integrated into run-trade

run-trade:
	@echo "💰 Running trading (mode determined by stage)..."
	poetry run alchemiser trade

# Removed run-trade-live - trading mode now determined by deployment stage

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

type-check:
	@echo "🔍 Running MyPy type checking (matching VS Code configuration)..."
	poetry run mypy the_alchemiser/ --config-file=pyproject.toml

typing-audit:
	@echo "🔍 Running typing architecture audit..."
	poetry run python tools/typing_audit.py

import-check:
	@echo "🔍 Checking module dependency rules..."
	poetry run lint-imports

migration-check: lint type-check typing-audit import-check
	@echo "🚀 Running full migration validation suite..."
	@echo "✅ Migration validation complete!"

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
