# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help clean format type-check import-check migration-check deploy-dev deploy-prod bump-patch bump-minor bump-major version deploy-ephemeral destroy-ephemeral list-ephemeral logs strategy-add strategy-add-from-config strategy-list strategy-sync strategy-list-dynamo strategy-check-fractionable validate-data-lake validate-dynamo validate-signals debug-strategy debug-strategy-historical rebalance-weights pnl-report

# Python path setup for scripts (mirrors Lambda layer structure)
export PYTHONPATH := $(shell pwd)/layers/shared:$(PYTHONPATH)

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
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
	@echo "Data Validation:"
	@echo "  validate-data-lake                   Validate S3 data lake against yfinance + Alpaca"
	@echo "  validate-data-lake symbols=SPY,QQQ   Validate specific symbols"
	@echo "  validate-data-lake mark-bad=1        Mark failed symbols for refetch"
	@echo "  validate-data-lake debug=1           Show detailed debug output"
	@echo "  validate-dynamo                      Validate DynamoDB data quality"
	@echo "  validate-dynamo stage=dev            Validate dev environment data"
	@echo "  validate-signals                     Validate signals vs Composer.trade"
	@echo "  validate-signals stage=prod          Validate prod signals"
	@echo ""
	@echo "Performance Reports:"
	@echo "  pnl-report                           Generate deposit-adjusted P&L report"
	@echo "  quantstats                           Generate QuantStats reports (prod)"
	@echo "  quantstats stage=dev                 Generate for dev environment"
	@echo "  quantstats days=180                  Custom lookback period (default: 90)"
	@echo ""
	@echo "Portfolio Management:"
	@echo "  rebalance-weights                    Recalculate strategy weights (Calmar-tilt)"
	@echo "  rebalance-weights dry-run=1          Preview without updating config"
	@echo "  rebalance-weights csv=path/to.csv    Use specific CSV file"
	@echo "  rebalance-weights stage=dev          Target dev/staging/prod (default: prod)"
	@echo ""
	@echo "Strategy Debugging:"
	@echo "  debug-strategy s=<name>              Debug strategy with full condition tracing"
	@echo "  debug-strategy list=1                List all available strategies"
	@echo "  debug-strategy-historical s=<name> as-of=<date>  Debug with historical data cutoff"
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
	@echo "  clean           Clean build artifacts"
	@echo ""
	@echo "Deployment (via GitHub Actions CI/CD):"
	@echo "  deploy-dev      Deploy to DEV (creates beta tag, triggers CI/CD)"
	@echo "  deploy-staging  Deploy to STAGING (creates staging tag, triggers CI/CD)"
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

# Status command removed - use programmatic access via TradingSystem class

# Development
format:
	@echo "🎨 Formatting code (Ruff formatter + auto-fix lint)..."
	@echo "  → Running Ruff formatter (handles whitespace, line endings, style)..."
	poetry run ruff format functions/ layers/shared/the_alchemiser/
	@echo "  → Running Ruff auto-fix (safe fixes for lints)..."
	poetry run ruff check --fix functions/ layers/shared/the_alchemiser/

type-check:
	@echo "🔍 Running MyPy type checking..."
	@# Check shared layer with correct module path
	@echo "  → Checking shared layer..."
	MYPYPATH="layers/shared" poetry run mypy layers/shared/the_alchemiser/ --config-file=pyproject.toml
	@# Check each Lambda function with its own MYPYPATH context
	@echo "  → Checking Lambda functions..."
	@for func in execution portfolio strategy_worker strategy_orchestrator strategy_aggregator trade_aggregator notifications data metrics; do \
		if [ -d "functions/$$func" ]; then \
			echo "    → functions/$$func"; \
			MYPYPATH="functions/$$func:layers/shared" poetry run mypy "functions/$$func/" --config-file=pyproject.toml 2>&1 | grep -v "^Success" || true; \
		fi; \
	done
	@echo "✅ Type checking complete"

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
	@OLD_VERSION=$$(poetry version -s); \
	poetry version patch; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	echo "📦 Staging version file..."; \
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
		echo "📤 Pushing to origin..."; \
		git push origin HEAD; \
	fi

bump-minor:
	@echo "🔢 Bumping minor version..."
	@OLD_VERSION=$$(poetry version -s); \
	poetry version minor; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	echo "📦 Staging version file..."; \
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
		echo "📤 Pushing to origin..."; \
		git push origin HEAD; \
	fi

bump-major:
	@echo "🔢 Bumping major version..."
	@OLD_VERSION=$$(poetry version -s); \
	poetry version major; \
	NEW_VERSION=$$(poetry version -s); \
	echo "📋 Version bumped: $$OLD_VERSION -> $$NEW_VERSION"; \
	echo "📦 Staging version file..."; \
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
		echo "📤 Pushing to origin..."; \
		git push origin HEAD; \
	fi

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
# DATA VALIDATION
# ============================================================================

# Validate S3 data lake against yfinance and Alpaca (with Adjustment.ALL)
# Usage: make validate-data-lake                   # Validate all configured symbols
#        make validate-data-lake symbols=SPY,QQQ   # Validate specific symbols
#        make validate-data-lake mark-bad=1        # Mark failed symbols for refetch
#        make validate-data-lake debug=1           # Show detailed debug output
#        make validate-data-lake limit=5           # Limit symbols (for testing)
validate-data-lake:
	@echo "🔍 Validating S3 data lake against yfinance + Alpaca..."
	@ARGS=""; \
	if [ -n "$(symbols)" ]; then ARGS="$$ARGS --symbols $(symbols)"; fi; \
	if [ -n "$(mark-bad)" ]; then ARGS="$$ARGS --mark-bad"; fi; \
	if [ -n "$(debug)" ]; then ARGS="$$ARGS --debug"; fi; \
	if [ -n "$(limit)" ]; then ARGS="$$ARGS --limit $(limit)"; fi; \
	poetry run python scripts/validation/validate_data_lake.py $$ARGS

# Validate DynamoDB data quality for per-strategy performance metrics
# Usage: make validate-dynamo                      # Validate prod data (default)
#        make validate-dynamo stage=dev            # Validate dev data
#        make validate-dynamo verbose=1            # Show detailed output
#        make validate-dynamo json=1               # Output as JSON
validate-dynamo:
	@echo "🔍 Validating DynamoDB data quality..."
	@ARGS=""; \
	if [ -n "$(stage)" ]; then ARGS="$$ARGS --stage $(stage)"; fi; \
	if [ -n "$(verbose)" ]; then ARGS="$$ARGS --verbose"; fi; \
	if [ -n "$(json)" ]; then ARGS="$$ARGS --json"; fi; \
	poetry run python scripts/validation/validate_dynamo_data.py $$ARGS

# Generate QuantStats per-strategy performance reports
# Usage: make quantstats                           # Generate prod reports (default)
#        make quantstats stage=dev                 # Generate dev reports
#        make quantstats days=180                  # Custom lookback period
#        make quantstats local=1                   # Save locally (no S3 upload)
# Generate P&L report with deposit adjustments
# Usage: make pnl-report
pnl-report:
	@echo "📊 Generating deposit-adjusted P&L report..."
	poetry run python scripts/pnl_report.py

# Export daily P&L to local Excel file (OneDrive)
# Usage: make pnl-excel
pnl-excel:
	@echo "📊 Exporting daily P&L to Excel..."
	poetry run python scripts/pnl_report.py --excel

# Run P&L dashboard locally
# Usage: make pnl-dashboard
pnl-dashboard:
	@echo "📊 Starting P&L dashboard..."
	poetry run streamlit run scripts/pnl_dashboard.py

quantstats:
	@echo "📊 Generating QuantStats per-strategy reports..."
	@STAGE=$${stage:-prod}; \
	DAYS=$${days:-90}; \
	TABLE="alchemiser-$$STAGE-trade-ledger"; \
	BUCKET="alchemiser-$$STAGE-reports"; \
	echo "  Stage: $$STAGE"; \
	echo "  Table: $$TABLE"; \
	echo "  Bucket: $$BUCKET"; \
	echo "  Days lookback: $$DAYS"; \
	TRADE_LEDGER_TABLE=$$TABLE \
	REPORTS_BUCKET=$$BUCKET \
	DAYS_LOOKBACK=$$DAYS \
	ALPACA_KEY=$$(aws ssm get-parameter --name "/alchemiser/$$STAGE/alpaca_key" --with-decryption --query "Parameter.Value" --output text --no-cli-pager 2>/dev/null || echo "$$ALPACA_KEY") \
	ALPACA_SECRET=$$(aws ssm get-parameter --name "/alchemiser/$$STAGE/alpaca_secret" --with-decryption --query "Parameter.Value" --output text --no-cli-pager 2>/dev/null || echo "$$ALPACA_SECRET") \
	poetry run python scripts/generate_quantstats_reports.py

# Recalculate strategy weights using Calmar-tilt formula
# Usage: make rebalance-weights                    # Use latest CSV, update config, deploy to prod
#        make rebalance-weights dry-run=1          # Preview without updating (no deploy)
#        make rebalance-weights csv=path/to.csv    # Use specific CSV
#        make rebalance-weights stage=dev          # Target dev config (no deploy)
#        make rebalance-weights stage=staging      # Target staging config (no deploy)
#        make rebalance-weights alpha=0.5          # Custom alpha parameter
#        make rebalance-weights f-min=0.5          # Custom floor multiplier
#        make rebalance-weights f-max=2.0          # Custom cap multiplier
rebalance-weights:
	@echo "⚖️  Recalculating strategy weights using Calmar-tilt formula..."
	@ARGS=""; \
	STAGE="$${stage:-prod}"; \
	if [ -n "$(csv)" ]; then ARGS="$$ARGS --csv $(csv)"; fi; \
	if [ -n "$(dry-run)" ]; then ARGS="$$ARGS --dry-run"; fi; \
	if [ -n "$(alpha)" ]; then ARGS="$$ARGS --alpha $(alpha)"; fi; \
	if [ -n "$(f-min)" ]; then ARGS="$$ARGS --f-min $(f-min)"; fi; \
	if [ -n "$(f-max)" ]; then ARGS="$$ARGS --f-max $(f-max)"; fi; \
	if [ -n "$(stage)" ]; then ARGS="$$ARGS --stage $(stage)"; STAGE="$(stage)"; fi; \
	poetry run python scripts/rebalance_strategy_weights.py $$ARGS; \
	if [ $$? -eq 0 ] && [ -z "$(dry-run)" ] && [ "$$STAGE" = "prod" ]; then \
		echo ""; \
		echo "🚀 Strategy weights updated successfully!"; \
		echo "📦 Bumping version and deploying to production..."; \
		echo ""; \
		git add layers/shared/the_alchemiser/shared/config/strategy.prod.json; \
		$(MAKE) bump-patch && $(MAKE) deploy-prod; \
	elif [ $$? -eq 0 ] && [ -z "$(dry-run)" ] && [ "$$STAGE" != "prod" ]; then \
		echo ""; \
		echo "✅ Strategy weights updated for $$STAGE (no auto-deploy for non-prod)"; \
	fi

# Validate strategy signals against Composer.trade (shifted T-1 comparison)
# Captures today's live_signals, compares today's our_signals vs yesterday's live_signals
# Usage: make validate-signals                    # Validate latest dev session
#        make validate-signals stage=prod         # Validate latest prod session
#        make validate-signals session=<id>       # Validate specific session
#        make validate-signals fresh=1            # Start fresh (ignore previous captures)
validate-signals:
	@echo "🔍 Validating signals against Composer.trade..."
	@ARGS="--shifted"; \
	if [ -n "$(stage)" ]; then ARGS="$$ARGS --stage $(stage)"; else ARGS="$$ARGS --stage dev"; fi; \
	if [ "$(fresh)" = "1" ]; then ARGS="$$ARGS --fresh"; fi; \
	if [ -n "$(session)" ]; then ARGS="$$ARGS --session-id $(session)"; fi; \
	poetry run python scripts/validation/validate_signals.py $$ARGS

# ============================================================================
# STRATEGY DEBUGGING
# ============================================================================

# Debug a strategy with full condition tracing
# Usage: make debug-strategy s=simons_kmlm        # Debug specific strategy
#        make debug-strategy s=chicken_rice       # Debug another strategy
#        make debug-strategy list=1               # List all available strategies
debug-strategy:
	@if [ -n "$(list)" ]; then \
		echo "📋 Listing available strategies..."; \
		poetry run python scripts/debug_strategy.py --list; \
	elif [ -z "$(s)" ]; then \
		echo "❌ Usage: make debug-strategy s=<strategy_name>"; \
		echo "         make debug-strategy list=1"; \
		exit 1; \
	else \
		echo "🔬 Debugging strategy: $(s)"; \
		poetry run python scripts/debug_strategy.py $(s); \
	fi

# Test all strategies with historical (Jan 5) and live (Jan 6 + per-indicator) modes
# Usage: make test-all-strategies
#        make test-all-strategies detailed=1
#        make test-all-strategies historical-only=1
#        make test-all-strategies s=simons_kmlm
test-all-strategies:
	@ARGS=""; \
	if [ -n "$(s)" ]; then ARGS="$$ARGS --strategy $(s)"; fi; \
	if [ -n "$(detailed)" ]; then ARGS="$$ARGS --detailed"; fi; \
	if [ -n "$(historical-only)" ]; then ARGS="$$ARGS --historical-only"; fi; \
	if [ -n "$(live-only)" ]; then ARGS="$$ARGS --live-only"; fi; \
	poetry run python scripts/test_all_strategies.py $$ARGS

# Debug strategy with historical data cutoff
# Usage: make debug-strategy-historical s=simons_kmlm as-of=yesterday
#        make debug-strategy-historical s=simons_kmlm as-of=2026-01-06
debug-strategy-historical:
	@if [ -z "$(s)" ]; then \
		echo "❌ Usage: make debug-strategy-historical s=<strategy_name> as-of=<date>"; \
		echo "         as-of can be: YYYY-MM-DD, 'yesterday', 'today'"; \
		exit 1; \
	elif [ -z "$(as-of)" ]; then \
		echo "❌ Usage: make debug-strategy-historical s=<strategy_name> as-of=<date>"; \
		echo "         as-of can be: YYYY-MM-DD, 'yesterday', 'today'"; \
		exit 1; \
	else \
		echo "🔬 Debugging strategy: $(s) (as-of $(as-of))"; \
		poetry run python scripts/debug_strategy_historical.py $(s) --as-of "$(as-of)"; \
	fi

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
