# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help clean run-pnl-weekly run-pnl-monthly run-pnl-detailed format type-check import-check migration-check deploy-dev deploy-prod bump-patch bump-minor bump-major version deploy-ephemeral destroy-ephemeral list-ephemeral logs backtest

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
	@echo ""
	@echo "P&L Analysis Commands:"
	@echo "  run-pnl-weekly  Show weekly P&L report"
	@echo "  run-pnl-monthly Show monthly P&L report"
	@echo "  run-pnl-detailed Show detailed monthly P&L report"
	@echo ""
	@echo "Backtesting:"
	@echo "  backtest strategy=<path> start=<date> end=<date>  Run single strategy backtest"
	@echo "  backtest portfolio=<config> start=<date> end=<date>  Run portfolio backtest"
	@echo "  backtest ... report=1      Generate HTML report"
	@echo "  backtest ... fetch=1       Pre-fetch missing data"
	@echo ""
	@echo "Observability:"
	@echo "  logs id=<correlation-id>  Fetch workflow logs (errors/warnings)"
	@echo "  logs id=<id> all=1        Fetch all logs for a workflow"
	@echo "  logs id=<id> stage=prod   Fetch logs from production"
	@echo ""
	@echo "Development:"
	@echo "  format          Format code with Ruff (style, whitespace, auto-fixes)"
	@echo "  type-check      Run MyPy type checking"
	@echo "  import-check    Check module dependency rules"
	@echo "  clean           Clean build artifacts"
	@echo ""
	@echo "Deployment (via GitHub Actions CI/CD):"
	@echo "  deploy-dev      Deploy to DEV (creates beta tag, triggers CI/CD)"
	@echo "  deploy-prod     Deploy to PROD (creates release tag, triggers CI/CD)"
	@echo "  deploy-prod v=x.y.z  Deploy specific version to PROD"
	@echo ""
	@echo "Version Management:"
	@echo "  bump-patch      Bump patch version (x.y.z -> x.y.z+1)"
	@echo "  bump-minor      Bump minor version (x.y.z -> x.y+1.0)"
	@echo "  bump-major      Bump major version (x.y.z -> x+1.0.0)"
	@echo "  version         Show current version"

# Setup & Installation

# Trading Commands (using the CLI)
# run-signals command removed - signal analysis is now integrated into run-trade

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

# Status command removed - use programmatic access via TradingSystem class

# Development
format:
	@echo "🎨 Formatting code (Ruff formatter + auto-fix lint)..."
	@echo "  → Running Ruff formatter (handles whitespace, line endings, style)..."
	poetry run ruff format the_alchemiser/
	@echo "  → Running Ruff auto-fix (safe fixes for lints)..."
	poetry run ruff check --fix the_alchemiser/

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

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .aws-sam/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Version Management
version:
	@echo "📋 Current version: $$(poetry version -s)"

bump-patch:
	@echo "🔢 Bumping patch version..."
	@# Check if there are unstaged changes
	@if ! git diff --quiet; then \
		echo ""; \
		echo "⚠️  Warning: You have unstaged changes that won't be included in the version bump commit."; \
		echo "💡 Stage them first with: git add <files>"; \
		echo ""; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo ""; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			exit 1; \
		fi; \
	fi; \
	OLD_VERSION=$$(poetry version -s); \
	poetry version patch; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	CHANGED=0; \
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
		CHANGED=1; \
	fi; \
	if [ $$CHANGED -eq 1 ]; then \
		echo "📤 Pushing commit to origin (current branch)..."; \
		git push origin HEAD; \
	fi

bump-minor:
	@echo "🔢 Bumping minor version..."
	@# Check if there are unstaged changes
	@if ! git diff --quiet; then \
		echo ""; \
		echo "⚠️  Warning: You have unstaged changes that won't be included in the version bump commit."; \
		echo "💡 Stage them first with: git add <files>"; \
		echo ""; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo ""; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			exit 1; \
		fi; \
	fi; \
	OLD_VERSION=$$(poetry version -s); \
	poetry version minor; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	CHANGED=0; \
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
		CHANGED=1; \
	fi; \
	if [ $$CHANGED -eq 1 ]; then \
		echo "📤 Pushing commit to origin (current branch)..."; \
		git push origin HEAD; \
	fi

bump-major:
	@echo "🔢 Bumping major version..."
	@# Check if there are unstaged changes
	@if ! git diff --quiet; then \
		echo ""; \
		echo "⚠️  Warning: You have unstaged changes that won't be included in the version bump commit."; \
		echo "💡 Stage them first with: git add <files>"; \
		echo ""; \
		read -p "Continue anyway? [y/N] " -n 1 -r; \
		echo ""; \
		if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
			exit 1; \
		fi; \
	fi; \
	OLD_VERSION=$$(poetry version -s); \
	poetry version major; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	CHANGED=0; \
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
		CHANGED=1; \
	fi; \
	if [ $$CHANGED -eq 1 ]; then \
		echo "📤 Pushing commit to origin (current branch)..."; \
		git push origin HEAD; \
	fi

# ============================================================================
# BACKTESTING
# ============================================================================

# Run backtests on DSL strategies
# Usage (single strategy):
#   make backtest strategy=strategies/dev/beam.clj start=2024-01-01 end=2024-12-01
#   make backtest strategy=strategies/dev/beam.clj start=2024-01-01 end=2024-12-01 capital=50000
#   make backtest strategy=strategies/dev/beam.clj start=2024-01-01 end=2024-12-01 report=1
#   make backtest strategy=strategies/dev/beam.clj start=2024-01-01 end=2024-12-01 fetch=1
#
# Usage (portfolio):
#   make backtest portfolio=the_alchemiser/config/strategy.dev.json start=2024-01-01 end=2024-12-01
#   make backtest portfolio=the_alchemiser/config/strategy.dev.json start=2024-01-01 end=2024-12-01 report=1
backtest:
	@if [ -z "$(start)" ] || [ -z "$(end)" ]; then \
		echo "❌ Missing required parameters!"; \
		echo ""; \
		echo "Usage (single strategy):"; \
		echo "  make backtest strategy=<path.clj> start=<YYYY-MM-DD> end=<YYYY-MM-DD>"; \
		echo ""; \
		echo "Usage (portfolio):"; \
		echo "  make backtest portfolio=<config.json> start=<YYYY-MM-DD> end=<YYYY-MM-DD>"; \
		echo ""; \
		echo "Options:"; \
		echo "  capital=<amount>   Initial capital (default: 100000)"; \
		echo "  report=1           Generate HTML report"; \
		echo "  pdf=1              Generate PDF report"; \
		echo "  fetch=1            Pre-fetch missing data before backtest"; \
		echo "  autofetch=1        Auto-fetch missing data during backtest"; \
		echo "  output=<file.json> Save results to JSON file"; \
		echo "  csv=<file.csv>     Save equity curve to CSV"; \
		echo "  verbose=1          Enable verbose output"; \
		echo ""; \
		exit 1; \
	fi; \
	ARGS="--start $(start) --end $(end)"; \
	if [ -n "$(strategy)" ]; then \
		ARGS="$(strategy) $$ARGS"; \
	elif [ -n "$(portfolio)" ]; then \
		ARGS="$(portfolio) --portfolio $$ARGS"; \
	else \
		echo "❌ Must specify either strategy=<path> or portfolio=<config>"; \
		exit 1; \
	fi; \
	if [ -n "$(capital)" ]; then ARGS="$$ARGS --capital $(capital)"; fi; \
	if [ -n "$(report)" ]; then ARGS="$$ARGS --report"; fi; \
	if [ -n "$(pdf)" ]; then ARGS="$$ARGS --pdf"; fi; \
	if [ -n "$(fetch)" ]; then ARGS="$$ARGS --fetch-data"; fi; \
	if [ -n "$(autofetch)" ]; then ARGS="$$ARGS --auto-fetch"; fi; \
	if [ -n "$(output)" ]; then ARGS="$$ARGS --output $(output)"; fi; \
	if [ -n "$(csv)" ]; then ARGS="$$ARGS --csv $(csv)"; fi; \
	if [ -n "$(verbose)" ]; then ARGS="$$ARGS --verbose"; fi; \
	poetry run python scripts/run_backtest.py $$ARGS

# ============================================================================
# OBSERVABILITY
# ============================================================================

# Fetch workflow logs by correlation_id
# Usage: make logs id=workflow-abc123
#        make logs id=workflow-abc123 all=1
#        make logs id=workflow-abc123 stage=prod
#        make logs id=workflow-abc123 all=1 verbose=1
logs:
	@if [ -z "$(id)" ]; then \
		echo "❌ Missing correlation/session id!"; \
		echo ""; \
		echo "Usage: make logs id=<correlation-id>"; \
		echo "       make logs id=<id> all=1        # Show all logs, not just errors"; \
		echo "       make logs id=<id> stage=prod   # Query production environment"; \
		echo "       make logs id=<id> verbose=1    # Include raw/debug logs"; \
		echo ""; \
		exit 1; \
	fi; \
	ARGS="--correlation-id $(id)"; \
	if [ -n "$(stage)" ]; then ARGS="$$ARGS --stage $(stage)"; fi; \
	if [ -n "$(all)" ]; then ARGS="$$ARGS --all"; fi; \
	if [ -n "$(verbose)" ]; then ARGS="$$ARGS --verbose"; fi; \
	if [ -n "$(output)" ]; then ARGS="$$ARGS --output $(output)"; fi; \
	poetry run python scripts/fetch_workflow_logs.py $$ARGS

# ============================================================================
# DEPLOYMENT (via GitHub Actions CI/CD)
# ============================================================================

# Dev Deployment - creates beta tag, triggers CI/CD
deploy-dev:
	@echo "🧪 Deploying to DEV environment..."
	@if [ -n "$(v)" ]; then \
		VERSION_TO_USE="$(v)"; \
		echo "📋 Using specified version: $$VERSION_TO_USE"; \
	else \
		VERSION_TO_USE=$$(poetry version -s); \
		echo "📋 Using version from pyproject.toml: $$VERSION_TO_USE"; \
	fi; \
	BETA_NUM=$$(git tag -l "v$$VERSION_TO_USE-beta.*" | wc -l | tr -d ' '); \
	BETA_NUM=$$((BETA_NUM + 1)); \
	TAG="v$$VERSION_TO_USE-beta.$$BETA_NUM"; \
	echo "🏷️ Tag: $$TAG (beta release for DEV environment)"; \
	echo ""; \
	if git tag | grep -q "^$$TAG$$"; then \
		echo "❌ Tag $$TAG already exists!"; \
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
	echo "📝 Creating beta tag $$TAG..."; \
	git tag -a "$$TAG" -m "Beta release $$TAG for dev deployment"; \
	echo "📤 Pushing tag to origin..."; \
	git push origin "$$TAG"; \
	echo "🚀 Creating GitHub pre-release..."; \
	gh release create "$$TAG" \
		--title "Beta Release $$TAG" \
		--notes "Beta release $$TAG for dev environment deployment" \
		--prerelease; \
	echo "✅ Beta pre-release $$TAG created successfully!"; \
	echo "🚀 Dev deployment will start automatically via GitHub Actions"

# Production Deployment - creates release tag, triggers CI/CD
deploy-prod:
	@echo "🚀 Creating production release tag..."
	@if [ -n "$(v)" ]; then \
		VERSION_TO_USE="$(v)"; \
		echo "📋 Using specified version: $$VERSION_TO_USE"; \
	else \
		VERSION_TO_USE=$$(poetry version -s); \
		echo "📋 Using version from pyproject.toml: $$VERSION_TO_USE"; \
	fi; \
	TAG="v$$VERSION_TO_USE"; \
	echo "🏷️ Tag: $$TAG (production release)"; \
	echo ""; \
	if git tag | grep -q "^$$TAG$$"; then \
		echo "❌ Tag $$TAG already exists!"; \
		echo "💡 Use a different version or delete the existing tag"; \
		exit 1; \
	fi; \
	echo "🔍 Checking for uncommitted changes..."; \
	if ! git diff --quiet || ! git diff --cached --quiet; then \
		echo "❌ You have uncommitted changes!"; \
		echo "💡 Please commit or stash your changes first"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "⚠️  WARNING: This will trigger a PRODUCTION deployment!"; \
	read -p "Are you sure you want to deploy v$$VERSION_TO_USE to PRODUCTION? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Production deployment cancelled"; \
		exit 1; \
	fi; \
	echo "📝 Creating production tag $$TAG..."; \
	git tag -a "$$TAG" -m "Production release $$TAG"; \
	echo "📤 Pushing tag to origin (will trigger prod deployment)..."; \
	git push origin "$$TAG"; \
	echo "✅ Production tag $$TAG created and pushed!"; \
	echo "🚀 Production deployment will start automatically via GitHub Actions"
