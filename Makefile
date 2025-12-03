# The Alchemiser Makefile
# Quick commands for development and deployment

.PHONY: help clean run-pnl-weekly run-pnl-monthly run-pnl-detailed format type-check import-check migration-check release bump-patch bump-minor bump-major version release-beta deploy-dev deploy-prod deploy-ephemeral destroy-ephemeral list-ephemeral

# Default target
help:
	@echo "🧪 The Alchemiser - Development Commands"
	@echo ""
	@echo "P&L Analysis Commands:"
	@echo "  run-pnl-weekly  Show weekly P&L report"
	@echo "  run-pnl-monthly Show monthly P&L report"
	@echo "  run-pnl-detailed Show detailed monthly P&L report"
	@echo ""
	@echo "Development:"
	@echo "  format          Format code with Ruff (style, whitespace, auto-fixes)"
	@echo "  type-check      Run MyPy type checking"
	@echo "  import-check    Check module dependency rules"
	@echo "  migration-check Full migration validation suite"
	@echo "  clean           Clean build artifacts"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-dev      Create and push beta tag to trigger dev deployment"
	@echo "  deploy-prod     Create and push release tag to trigger prod deployment"
	@echo "  deploy-ephemeral Deploy ephemeral stack (TTL_HOURS=24, optionally BRANCH=...)"
	@echo "  destroy-ephemeral Destroy ephemeral stack (STACK=alchemiser-ephem-...)"
	@echo "  list-ephemeral  List all ephemeral stacks"
	@echo "  release         Create and push a production release tag (same as deploy-prod)"
	@echo "  release-beta    Create and push a beta release tag (same as deploy-dev)"
	@echo "  release v=x.y.z Create release with specific version number"
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

migration-check: type-check import-check
	@echo "🚀 Running full migration validation suite..."
	@echo "✅ Migration validation complete!"

clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .aws-sam/
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
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
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
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
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
	git add pyproject.toml; \
	if git diff --cached --quiet; then \
		echo "ℹ️  No changes to commit (version already at $$NEW_VERSION)"; \
	else \
		git commit -m "Bump version to $$NEW_VERSION"; \
	fi

# Beta/Dev Deployment
release-beta:
	@echo "🧪 Creating beta release for dev deployment..."
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

deploy-dev: release-beta

# Production Deployment
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

# Microservices deployment targets
.PHONY: deploy-microservices-dev
deploy-microservices-dev: ## Deploy microservices to dev environment
	@echo "Deploying microservices to dev..."
	@./scripts/deploy-microservices.sh dev

.PHONY: deploy-microservices-prod
deploy-microservices-prod: ## Deploy microservices to prod environment
	@echo "Deploying microservices to prod..."
	@./scripts/deploy-microservices.sh prod

.PHONY: release-microservices-beta
release-microservices-beta: bump-patch ## Create beta release tag for microservices
	@$(eval VERSION := $(shell $(PYTHON) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['tool']['poetry']['version'])"))
	@$(eval BETA_VERSION := $(VERSION)-microservices-beta.$(shell date +%Y%m%d%H%M%S))
	@echo "Creating microservices beta release: v$(BETA_VERSION)"
	@git tag -a "v$(BETA_VERSION)" -m "Microservices beta release v$(BETA_VERSION)"
	@git push origin "v$(BETA_VERSION)"
	@echo "✅ Microservices beta tag v$(BETA_VERSION) created and pushed"

.PHONY: release-microservices
release-microservices: bump-minor ## Create release tag for microservices
	@$(eval VERSION := $(shell $(PYTHON) -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['tool']['poetry']['version'])"))
	@echo "Creating microservices release: v$(VERSION)-microservices"
	@git tag -a "v$(VERSION)-microservices" -m "Microservices release v$(VERSION)"
	@git push origin "v$(VERSION)-microservices"
	@echo "✅ Microservices tag v$(VERSION)-microservices created and pushed"

# Ephemeral Deployment
deploy-ephemeral:
	@echo "🧪 Deploying ephemeral stack..."
	@TTL_HOURS=$${TTL_HOURS:-24}; \
	BRANCH=$${BRANCH:-$$(git branch --show-current)}; \
	echo "Branch: $$BRANCH"; \
	echo "TTL: $$TTL_HOURS hours"; \
	echo ""; \
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
	echo "🚀 Triggering ephemeral deployment via GitHub Actions..."; \
	echo "💡 Select branch '$$BRANCH' in the GitHub Actions UI"; \
	gh workflow run manual-deploy-ephemeral.yml \
		--ref "$$BRANCH" \
		-f ttl_hours="$$TTL_HOURS"; \
	echo ""; \
	echo "✅ Deployment triggered!"; \
	echo "📊 View progress: gh run list --workflow=manual-deploy-ephemeral.yml"; \
	echo "📋 Or visit: https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/manual-deploy-ephemeral.yml"

# Destroy Ephemeral Stack
destroy-ephemeral:
	@echo "🗑️  Destroying ephemeral stack..."
	@if [ -z "$(STACK)" ]; then \
		echo "❌ ERROR: STACK parameter is required"; \
		echo "💡 Usage: make destroy-ephemeral STACK=alchemiser-ephem-feature-foo-a1b2c3d"; \
		echo ""; \
		echo "📋 List available stacks with: make list-ephemeral"; \
		exit 1; \
	fi; \
	if [[ ! "$(STACK)" =~ ^alchemiser-ephem- ]]; then \
		echo "❌ ERROR: Stack name must start with 'alchemiser-ephem-'"; \
		echo "💡 This prevents accidental deletion of dev/prod stacks"; \
		exit 1; \
	fi; \
	echo "Stack: $(STACK)"; \
	echo ""; \
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
	echo "⚠️  WARNING: This will permanently delete the ephemeral stack: $(STACK)"; \
	read -p "Are you sure? [y/N] " -n 1 -r; \
	echo ""; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Destruction cancelled"; \
		exit 1; \
	fi; \
	echo "🗑️  Triggering stack deletion via GitHub Actions..."; \
	gh workflow run manual-destroy-ephemeral.yml \
		-f stack_name="$(STACK)"; \
	echo ""; \
	echo "✅ Deletion triggered!"; \
	echo "📊 View progress: gh run list --workflow=manual-destroy-ephemeral.yml"; \
	echo "📋 Or visit: https://github.com/Josh-moreton/alchemiser-quant/actions/workflows/manual-destroy-ephemeral.yml"

# List Ephemeral Stacks
list-ephemeral:
	@echo "📋 Listing ephemeral stacks..."
	@if ! command -v aws >/dev/null 2>&1; then \
		echo "❌ AWS CLI is not installed!"; \
		echo "💡 Install with: pip install awscli"; \
		exit 1; \
	fi; \
	echo ""; \
	aws cloudformation describe-stacks \
		--query "Stacks[?Tags[?Key=='Ephemeral' && Value=='true']].{Name:StackName,Status:StackStatus,Created:CreationTime,Branch:Tags[?Key=='Branch']|[0].Value,TTL:Tags[?Key=='TTLHours']|[0].Value}" \
		--output table 2>/dev/null || { \
		echo "⚠️  Failed to list stacks. Check AWS credentials."; \
		echo "💡 Ensure you are authenticated: aws configure"; \
		exit 1; \
	}; \
	echo ""; \
	echo "💡 To destroy a stack: make destroy-ephemeral STACK=<stack-name>"
