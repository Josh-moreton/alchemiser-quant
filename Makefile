# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help install dev clean run-trade status deploy format lint type-check import-check migration-check test test-unit test-integration test-functional test-e2e test-all

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install         Install package in development mode"
	@echo "  dev             Install with development dependencies"
	@echo ""
	@echo "Trading Commands:"
	@echo "  run-trade       Execute trading via python -m the_alchemiser"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test            Run all tests"
	@echo "  test-unit       Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-functional Run functional tests only"
	@echo "  test-e2e        Run end-to-end tests only"
	@echo "  test-all        Run comprehensive test suite with coverage"
	@echo ""
	@echo "Development:"
	@echo "  format          Format code with Ruff (formatter + fixes)"
	@echo "  lint            Run linting"
	@echo "  type-check      Run MyPy type checking"
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

# Testing Commands
test:
	@echo "🧪 Running all tests..."
	python -m pytest tests/ -v

test-unit:
	@echo "🔬 Running unit tests..."
	python -m pytest -m unit tests/ -v

test-integration:
	@echo "🔗 Running integration tests..."
	python -m pytest -m integration tests/ -v

test-functional:
	@echo "⚙️ Running functional tests..."
	python -m pytest -m functional tests/ -v

test-e2e:
	@echo "🚀 Running end-to-end tests..."
	python -m pytest -m e2e tests/ -v

test-all:
	@echo "🧪 Running comprehensive test suite..."
	python -m pytest tests/ -v --tb=short
	@echo "✅ Test suite completed!"

# Trading Commands (using the CLI)
# run-signals command removed - signal analysis is now integrated into run-trade

run-trade:
	@echo "💰 Running trading (mode determined by stage)..."
	python -m the_alchemiser

# Removed run-trade-live - trading mode now determined by deployment stage

# Status command removed - use programmatic access via TradingSystem class

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

import-check:
	@echo "🔍 Checking module dependency rules..."
	poetry run importlinter --config pyproject.toml

migration-check: lint type-check import-check
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
	bash scripts/deploy.sh
