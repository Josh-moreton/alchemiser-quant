# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help install dev clean run-trade status deploy format lint type-check import-check migration-check test test-unit test-integration test-functional test-e2e test-all test-coverage release bump-patch bump-minor bump-major version stress-test stress-test-quick stress-test-stateful stress-test-stateful-quick stress-test-dry-run

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
	@echo "P&L Analysis Commands:"
	@echo "  run-pnl-weekly  Show weekly P&L report"
	@echo "  run-pnl-monthly Show monthly P&L report"
	@echo "  run-pnl-detailed Show detailed monthly P&L report"
	@echo ""
	@echo "Stress Testing Commands:"
	@echo "  stress-test              Run full stress test (~34 scenarios, liquidation mode)"
	@echo "  stress-test-quick        Run quick stress test (~14 scenarios, liquidation mode)"
	@echo "  stress-test-stateful     Run full stress test in stateful mode (maintains portfolio)"
	@echo "  stress-test-stateful-quick Run quick stress test in stateful mode"
	@echo "  stress-test-dry-run      Show stress test plan without executing"
	@echo ""
	@echo "Backtesting Commands:"
	@echo "  backtest-download        Download historical data for backtesting"
	@echo "  backtest                 Run backtest (default 14 days / 2 weeks)"
	@echo "  backtest-range           Run backtest with custom date range"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test            Run all tests"
	@echo "  test-unit       Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-functional Run functional tests only"
	@echo "  test-e2e        Run end-to-end tests only"
	@echo "  test-all        Run comprehensive test suite with coverage"
	@echo "  test-coverage   Run tests with coverage report (XML for SonarCloud)"
	@echo "  stress-test     Run comprehensive trading system stress test"
	@echo "  stress-test-quick Run quick stress test (subset of scenarios)"
	@echo "  stress-test-dry-run Run stress test dry run (show plan only)"
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
	@echo "  release         Create and push a GitHub release (uses version from pyproject.toml)"
	@echo "  release v=x.y.z Create release with specific version number"
	@echo ""
	@echo "Version Management:"
	@echo "  bump-patch      Bump patch version (x.y.z -> x.y.z+1)"
	@echo "  bump-minor      Bump minor version (x.y.z -> x.y+1.0)"
	@echo "  bump-major      Bump major version (x.y.z -> x+1.0.0)"
	@echo "  version         Show current version"

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

test-coverage:
	@echo "📊 Running tests with coverage report for SonarCloud..."
	@# Ensure pytest-cov is available (installed via dev dependencies)
	@poetry run python -c "import pytest_cov" >/dev/null 2>&1 || { \
		echo "❌ pytest-cov not found in the Poetry env."; \
		echo "💡 Run: poetry install --with dev"; \
		exit 1; \
	}
	poetry run pytest --cov=the_alchemiser --cov-report=xml --cov-report=term --ignore=tests/e2e -v tests/
	@echo "✅ Coverage report generated: coverage.xml"

# Stress Testing Commands

# Trading Commands (using the CLI)
# run-signals command removed - signal analysis is now integrated into run-trade

run-trade:
	@echo "💰 Running trading (mode determined by stage)..."
	poetry run python -m the_alchemiser

# P&L Analysis Commands
run-pnl-weekly:
	@echo "📊 Running weekly P&L analysis..."
	poetry run python -m the_alchemiser pnl --weekly

run-pnl-monthly:
	@echo "📊 Running monthly P&L analysis..."
	poetry run python -m the_alchemiser pnl --monthly

run-pnl-detailed:
	@echo "📊 Running detailed monthly P&L analysis..."
	poetry run python -m the_alchemiser pnl --monthly --detailed

# Stress Testing Commands
stress-test:
	@echo "🔥 Running full stress test (liquidation mode)..."
	poetry run python scripts/stress_test.py

stress-test-quick:
	@echo "🔥 Running quick stress test (liquidation mode)..."
	poetry run python scripts/stress_test.py --quick

stress-test-stateful:
	@echo "🔥 Running full stress test (stateful mode - maintains portfolio)..."
	poetry run python scripts/stress_test.py --stateful

stress-test-stateful-quick:
	@echo "🔥 Running quick stress test (stateful mode - maintains portfolio)..."
	poetry run python scripts/stress_test.py --stateful --quick

stress-test-dry-run:
	@echo "🔥 Showing stress test execution plan..."
	poetry run python scripts/stress_test.py --dry-run

# Backtesting Commands
backtest-download:
	@echo "📊 Downloading historical data for backtesting..."
	poetry run python scripts/backtest_download.py

backtest:
	@echo "📊 Running backtest (default 14 days / 2 weeks)..."
	poetry run python scripts/backtest_run.py

backtest-range:
	@echo "📊 Running backtest with custom date range..."
	@echo "Usage: make backtest-range ARGS='--start-date 2023-01-01 --end-date 2023-12-31'"
	poetry run python scripts/backtest_run.py $(ARGS)

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
	# Detect available Import Linter entrypoint and run with pyproject.toml
	@ENTRY=$$(poetry run python -c "import shutil; print(shutil.which('lint-imports') or '')"); \
	if [ -n "$$ENTRY" ]; then \
		poetry run lint-imports --config pyproject.toml; \
	else \
		poetry run python -m importlinter --config pyproject.toml; \
	fi

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

release:
	@echo "🏷️ Creating GitHub release..."
	@if [ -n "$(v)" ]; then \
		VERSION_TO_USE="$(v)"; \
		echo "📋 Using specified version: $$VERSION_TO_USE"; \
	else \
		VERSION_TO_USE=$$(poetry version -s); \
		echo "📋 Using version from pyproject.toml: $$VERSION_TO_USE"; \
	fi; \
	TAG="v$$VERSION_TO_USE"; \
	echo "🏷️ Tag: $$TAG"; \
	echo ""; \
	if git tag | grep -q "^$$TAG$$"; then \
		echo "❌ Tag $$TAG already exists!"; \
		echo "💡 Use a different version or delete the existing tag"; \
		exit 1; \
	fi; \
	if ! command -v gh >/dev/null 2>&1; then \
		echo "❌ GitHub CLI (gh) is not installed!"; \
		echo "💡 Install with: brew install gh"; \
		exit 1; \
	fi; \
	if ! gh auth status >/dev/null 2>&1; then \
		echo "❌ GitHub CLI is not authenticated!"; \
		echo "💡 Run: gh auth login"; \
		exit 1; \
	fi; \
	echo "🔍 Checking for uncommitted changes..."; \
	if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "❌ You have uncommitted changes!"; \
		echo "💡 Please commit or stash your changes first"; \
		exit 1; \
	fi; \
	echo "📝 Creating tag $$TAG..."; \
	git tag -a "$$TAG" -m "Release $$TAG"; \
	echo "📤 Pushing tag to origin..."; \
	git push origin "$$TAG"; \
	echo "🚀 Creating GitHub release..."; \
	gh release create "$$TAG" \
		--title "Release $$TAG" \
		--notes "Release $$TAG of The Alchemiser" \
		--latest; \
	echo "✅ Release $$TAG created successfully!"

# Version Management
version:
	@echo "📋 Current version: $$(poetry version -s)"

bump-patch:
	@echo "🔢 Bumping patch version..."
	@OLD_VERSION=$$(poetry version -s); \
	poetry version patch; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	git add pyproject.toml; \
	git commit -m "Bump version to $$NEW_VERSION"

bump-minor:
	@echo "🔢 Bumping minor version..."
	@OLD_VERSION=$$(poetry version -s); \
	poetry version minor; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	git add pyproject.toml; \
	git commit -m "Bump version to $$NEW_VERSION"

bump-major:
	@echo "🔢 Bumping major version..."
	@OLD_VERSION=$$(poetry version -s); \
	poetry version major; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	git add pyproject.toml; \
	git commit -m "Bump version to $$NEW_VERSION"
