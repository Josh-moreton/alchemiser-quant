# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help clean sync-shared-layer run-pnl-weekly run-pnl-monthly run-pnl-detailed hourly-gain-analysis validate-s3 format type-check import-check migration-check deploy-dev deploy-prod deploy-data data-quality bump-patch bump-minor bump-major version deploy-ephemeral destroy-ephemeral list-ephemeral logs backtest strategy-add strategy-add-from-config strategy-list strategy-sync strategy-list-dynamo strategy-check-fractionable

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
	@echo ""
	@echo "P&L Analysis Commands:"
	@echo "  run-pnl-weekly  Show weekly P&L report"
	@echo "  run-pnl-monthly Show monthly P&L report"
	@echo "  run-pnl-detailed Show detailed monthly P&L report"
	@echo ""
	@echo "Market Analysis:"
	@echo "  hourly-gain-analysis              Analyze hourly gain/loss for SPY & QQQ (10 years)"
	@echo "  hourly-gain-analysis years=5      Custom lookback period"
	@echo "  hourly-gain-analysis symbols=...  Custom symbols (space-separated)"
	@echo ""
	@echo "Data Validation:"
	@echo "  validate-s3                        Validate S3 data against yfinance (all symbols)"
	@echo "  validate-s3 symbols=AAPL,MSFT     Validate specific symbols"
	@echo "  validate-s3 limit=50               Validate first 50 symbols"
	@echo "  validate-s3 limit=100 detailed=1  Validate with detailed discrepancies JSON"
	@echo ""
	@echo "Backtesting:"
	@echo "  backtest                             Run portfolio backtest (last 2 months, strategy.dev.json)"
	@echo "  backtest start=<date> end=<date>    Run with custom date range"
	@echo "  backtest ... config=<file>          Use custom config file"
	@echo "  backtest ... report=1               Generate HTML report"
	@echo "  backtest ... no-auto-fetch=1        Disable S3 auto-fetch (local only)"
	@echo ""
	@echo "Data Management:"
	@echo "  sync-data                            Sync all symbols from S3 to local"
	@echo "  sync-data force=1                   Force re-download all data"
	@echo "  seed-data                            Seed S3 from Alpaca (requires API keys)"
	@echo ""
	@echo "Strategy Ledger Management:"
	@echo "  strategy-add                         Add strategy to ledger interactively"
	@echo "  strategy-add-from-config            Add strategies from config (strategy.dev.json)"
	@echo "  strategy-add-from-config config=... Use custom config file"
	@echo "  strategy-list                        List all strategies in ledger"
	@echo "  strategy-sync                        Sync ledger to DynamoDB (dev)"
	@echo "  strategy-sync stage=prod            Sync ledger to DynamoDB (prod)"
	@echo "  strategy-list-dynamo                List strategies from DynamoDB (dev)"
	@echo "  strategy-list-dynamo stage=prod     List strategies from DynamoDB (prod)"
	@echo "  strategy-check-fractionable         Check fractionability (uses strategy.dev.json)"
	@echo "  strategy-check-fractionable config=strategy.prod.json"
	@echo "  strategy-check-fractionable all=1   Check all strategy files"
	@echo ""
	@echo "Observability:"
	@echo "  logs                       Fetch logs from most recent workflow (dev)"
	@echo "  logs stage=prod            Fetch logs from most recent workflow (prod)"
	@echo "  logs id=<correlation-id>   Fetch logs for specific workflow"
	@echo "  logs id=<id> all=1         Fetch all logs for a workflow"
	@echo ""
	@echo "Development:"
	@echo "  format          Format code with Ruff (style, whitespace, auto-fixes)"
	@echo "  type-check      Run MyPy type checking"
	@echo "  import-check    Check module dependency rules"
	@echo "  sync-shared-layer  Sync shared code to Lambda layer"
	@echo "  clean           Clean build artifacts"
	@echo ""
	@echo "Deployment (via GitHub Actions CI/CD):"
	@echo "  deploy-dev      Deploy to DEV (creates beta tag, triggers CI/CD)"
	@echo "  deploy-staging  Deploy to STAGING (creates staging tag, triggers CI/CD)"
	@echo "  deploy-prod     Deploy to PROD (creates release tag, triggers CI/CD)"
	@echo "  deploy-prod v=x.y.z  Deploy specific version to PROD"
	@echo ""
	@echo "Shared Data Infrastructure:"
	@echo "  deploy-data              Deploy shared datalake via GitHub Actions"
	@echo "                           (triggers workflow_dispatch manually)"
	@echo "  data-quality        Test data quality monitor Lambda (invokes in AWS)"
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

# Market Analysis Commands
hourly-gain-analysis:
	@echo "📊 Running hourly gain/loss analysis..."
	@YEARS=$${years:-10}; \
	SYMBOLS=$${symbols:-SPY QQQ}; \
	poetry run python scripts/hourly_gain_analysis.py --years $$YEARS --symbols $$SYMBOLS

# Validate S3 market data against yfinance
# Usage: make validate-s3                                    # All symbols
#        make validate-s3 symbols=AAPL,MSFT,GOOGL            # Specific symbols
#        make validate-s3 limit=50                           # First 50
#        make validate-s3 limit=100 detailed=1               # With detailed JSON report
#        make validate-s3 bucket=my-bucket region=us-west-2  # Custom S3
validate-s3:
	@echo "🔍 Validating S3 market data against yfinance..."
	@ARGS=""; \
	if [ -n "$(symbols)" ]; then ARGS="$$ARGS --symbols $(symbols)"; fi; \
	if [ -n "$(limit)" ]; then ARGS="$$ARGS --limit $(limit)"; fi; \
	if [ -n "$(output)" ]; then ARGS="$$ARGS --output $(output)"; else ARGS="$$ARGS --output s3_validation_report.csv"; fi; \
	if [ -n "$(detailed)" ]; then ARGS="$$ARGS --detailed s3_validation_discrepancies.json"; fi; \
	if [ -n "$(bucket)" ]; then ARGS="$$ARGS --bucket $(bucket)"; fi; \
	if [ -n "$(region)" ]; then ARGS="$$ARGS --region $(region)"; fi; \
	poetry run python scripts/validate_s3_against_yfinance.py $$ARGS && \
	echo "" && \
	echo "✅ Validation complete! Report: s3_validation_report.csv"

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

# Sync shared code to Lambda layer
sync-shared-layer:
	@echo "🔄 Syncing shared code to Lambda layer..."
	rm -rf layers/shared/python/the_alchemiser/shared
	mkdir -p layers/shared/python/the_alchemiser
	cp the_alchemiser/__init__.py layers/shared/python/the_alchemiser/
	cp -r the_alchemiser/shared layers/shared/python/the_alchemiser/
	@echo "✅ Shared code synced to layers/shared/"

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

# Run portfolio backtests
# Usage:
#   make backtest                                    # Last 2 months, strategy.dev.json
#   make backtest start=2024-01-01 end=2024-12-01   # Custom date range
#   make backtest config=the_alchemiser/config/strategy.prod.json
#   make backtest capital=50000 report=1
#   make backtest fetch=1

backtest:
	@ARGS=""; \
	if [ -n "$(config)" ]; then ARGS="$$ARGS --config $(config)"; fi; \
	if [ -n "$(start)" ]; then ARGS="$$ARGS --start $(start)"; fi; \
	if [ -n "$(end)" ]; then ARGS="$$ARGS --end $(end)"; fi; \
	if [ -n "$(capital)" ]; then ARGS="$$ARGS --capital $(capital)"; fi; \
	if [ -n "$(report)" ]; then ARGS="$$ARGS --report"; fi; \
	if [ -n "$(pdf)" ]; then ARGS="$$ARGS --pdf"; fi; \
	if [ -n "$(fetch)" ]; then ARGS="$$ARGS --fetch-data"; fi; \
	if [ -n "$$(echo '$(no-auto-fetch)' | tr -d ' ')" ]; then ARGS="$$ARGS --no-auto-fetch"; fi; \
	if [ -n "$(output)" ]; then ARGS="$$ARGS --output $(output)"; fi; \
	if [ -n "$(csv)" ]; then ARGS="$$ARGS --csv $(csv)"; fi; \
	if [ -n "$(verbose)" ]; then ARGS="$$ARGS --verbose"; fi; \
	poetry run python scripts/run_backtest.py $$ARGS

# Sync data from S3 to local storage
# Usage: make sync-data
#        make sync-data force=1  (re-download all)
sync-data:
	@echo "📥 Syncing market data from S3 to local..."
	@ARGS=""; \
	if [ -n "$(force)" ]; then ARGS="--force"; fi; \
	poetry run python -c "from the_alchemiser.backtest_v2.adapters.data_fetcher import BacktestDataFetcher; from pathlib import Path; f = BacktestDataFetcher(Path('data/historical')); r = f.sync_all_from_s3(force_full=$(if $(force),True,False)); print(f'Synced {sum(r.values())}/{len(r)} symbols')"

# Seed S3 from Alpaca (requires API credentials)
# Usage: make seed-data
seed-data:
	@echo "🌱 Seeding S3 from Alpaca..."
	@if [ -z "$${ALPACA__KEY:-$$ALPACA_KEY}" ] || [ -z "$${ALPACA__SECRET:-$$ALPACA_SECRET}" ]; then \
		echo "❌ Alpaca credentials not set!"; \
		echo "Set ALPACA__KEY and ALPACA__SECRET in your .env or environment"; \
		exit 1; \
	fi
	poetry run python scripts/seed_market_data.py

# ============================================================================
# STRATEGY LEDGER
# ============================================================================

# Add a strategy to the ledger interactively
# Usage: make strategy-add
strategy-add:
	@echo "📋 Adding strategy to ledger..."
	poetry run python scripts/strategy_ledger.py add

# Add all strategies from a config file to the ledger
# Usage: make strategy-add-from-config               # Uses strategy.dev.json
#        make strategy-add-from-config config=strategy.prod.json
strategy-add-from-config:
	@echo "📋 Adding strategies from config..."
	@CONFIG=$${config:-strategy.dev.json}; \
	poetry run python scripts/strategy_ledger.py add-from-config --config $$CONFIG

# List all strategies in the ledger
# Usage: make strategy-list
strategy-list:
	@poetry run python scripts/strategy_ledger.py list

# Sync strategy ledger to DynamoDB
# Usage: make strategy-sync                  # Sync to dev
#        make strategy-sync stage=prod       # Sync to prod
strategy-sync:
	@echo "🔄 Syncing strategy ledger to DynamoDB..."
	@STAGE=$${stage:-dev}; \
	poetry run python scripts/strategy_ledger.py sync --stage $$STAGE

# List strategies from DynamoDB
# Usage: make strategy-list-dynamo           # List from dev
#        make strategy-list-dynamo stage=prod
strategy-list-dynamo:
	@STAGE=$${stage:-dev}; \
	poetry run python scripts/strategy_ledger.py list-dynamo --stage $$STAGE

# Check which assets are not fractionable
# Usage: make strategy-check-fractionable                    # Uses strategy.dev.json
#        make strategy-check-fractionable config=strategy.prod.json
#        make strategy-check-fractionable verbose=1
#        make strategy-check-fractionable all=1               # Check all .clj files
strategy-check-fractionable:
	@echo "🔍 Checking asset fractionability..."
	@ARGS=""; \
	if [ -n "$(config)" ]; then ARGS="$$ARGS --config $(config)"; fi; \
	if [ -n "$(verbose)" ]; then ARGS="$$ARGS --verbose"; fi; \
	if [ -n "$(show-all)" ]; then ARGS="$$ARGS --show-all"; fi; \
	if [ -n "$(all)" ]; then ARGS="$$ARGS --all-strategies"; fi; \
	poetry run python scripts/check_fractionable_assets.py $$ARGS

# ============================================================================
# OBSERVABILITY
# ============================================================================

# Fetch workflow logs by correlation_id (or auto-detect most recent)
# Usage: make logs                        # Most recent workflow in dev
#        make logs stage=prod             # Most recent workflow in prod
#        make logs id=workflow-abc123     # Specific workflow
#        make logs id=<id> all=1          # All logs, not just errors
#        make logs id=<id> verbose=1      # Include raw/debug logs
logs:
	@ARGS=""; \
	if [ -n "$(id)" ]; then ARGS="$$ARGS --correlation-id $(id)"; fi; \
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

# Staging Deployment - creates staging tag, triggers CI/CD
deploy-staging:
	@echo "🔬 Deploying to STAGING environment..."
	@if [ -n "$(v)" ]; then \
		VERSION_TO_USE="$(v)"; \
		echo "📋 Using specified version: $$VERSION_TO_USE"; \
	else \
		VERSION_TO_USE=$$(poetry version -s); \
		echo "📋 Using version from pyproject.toml: $$VERSION_TO_USE"; \
	fi; \
	STAGING_NUM=$$(git tag -l "v$$VERSION_TO_USE-staging.*" | wc -l | tr -d ' '); \
	STAGING_NUM=$$((STAGING_NUM + 1)); \
	TAG="v$$VERSION_TO_USE-staging.$$STAGING_NUM"; \
	echo "🏷️ Tag: $$TAG (staging release for STAGING environment)"; \
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
	echo "📝 Creating staging tag $$TAG..."; \
	git tag -a "$$TAG" -m "Staging release $$TAG for staging deployment"; \
	echo "📤 Pushing tag to origin..."; \
	git push origin "$$TAG"; \
	echo "🚀 Creating GitHub pre-release..."; \
	gh release create "$$TAG" \
		--title "Staging Release $$TAG" \
		--notes "Staging release $$TAG for staging environment deployment" \
		--prerelease; \
	echo "✅ Staging pre-release $$TAG created successfully!"; \
	echo "🚀 Staging deployment will start automatically via GitHub Actions"

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
	echo "🚀 Creating GitHub production release..."; \
	gh release create "$$TAG" \
		--title "Release $$TAG" \
		--notes "Production release $$TAG"; \
	echo "✅ Production release $$TAG created and pushed!"; \
	echo "🚀 Production deployment will start automatically via GitHub Actions"

# Shared Data Infrastructure - triggers GitHub Actions workflow
deploy-data:
	@echo "📦 Deploying shared data infrastructure via GitHub Actions..."
	@if ! command -v gh >/dev/null 2>&1; then \
		echo "❌ GitHub CLI (gh) is not installed!"; \
		echo "💡 Install with: brew install gh"; \
		exit 1; \
	fi; \
	if ! gh auth status >/dev/null 2>&1; then \
		echo "❌ GitHub CLI is not authenticated!"; \
		echo "💡 Run: gh auth login"; \
		exit 1; \
	fi; \
	CURRENT_BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	echo "📍 Current branch: $$CURRENT_BRANCH"; \
	echo "🚀 Triggering deploy-shared-data workflow on branch $$CURRENT_BRANCH..."; \
	gh workflow run deploy-shared-data.yml --ref $$CURRENT_BRANCH --field confirm=deploy; \
	echo ""; \
	echo "✅ Workflow triggered! Check status at:"; \
	echo "   https://github.com/$$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions/workflows/deploy-shared-data.yml"

# Test Data Quality Monitor Lambda
# Usage: make data-quality
#        make data-quality stage=prod
data-quality:
	@echo "🧪 Testing data quality monitor Lambda..."
	@STAGE=$${stage:-dev}; \
	if [ "$$STAGE" = "dev" ]; then \
		FUNCTION_NAME="alchemiser-shared-data-quality-monitor"; \
		REGION="us-east-1"; \
	else \
		FUNCTION_NAME="alchemiser-shared-data-quality-monitor-$$STAGE"; \
		REGION="us-east-1"; \
	fi; \
	echo "📍 Function: $$FUNCTION_NAME"; \
	echo "📍 Region: $$REGION"; \
	echo ""; \
	echo "🚀 Invoking Lambda..."; \
	if aws lambda invoke \
		--function-name "$$FUNCTION_NAME" \
		--region "$$REGION" \
		--log-type Tail \
		/tmp/dqm-response.json 2>&1 | grep -q "StatusCode"; then \
		echo "✅ Lambda invoked successfully!"; \
		echo ""; \
		echo "📋 Response:"; \
		cat /tmp/dqm-response.json | jq . 2>/dev/null || cat /tmp/dqm-response.json; \
		echo ""; \
		rm -f /tmp/dqm-response.json; \
	else \
		echo "❌ Failed to invoke Lambda"; \
		echo "💡 Make sure the function is deployed and you have AWS credentials configured"; \
		exit 1; \
	fi
