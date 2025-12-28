# Coordinator Lambda Build
# Code is synced from source via root Makefile before SAM build

ARTIFACTS_DIR ?= $(shell pwd)

.PHONY: build build-StrategyOrchestratorFunction

build-StrategyOrchestratorFunction: build

build:
	@echo "📦 Building Coordinator Lambda..."
	if [ ! -d "the_alchemiser/coordinator_v2" ]; then \
		echo "❌ ERROR: coordinator_v2 not found. Run 'make sync-all' from repo root first."; \
		exit 1; \
	fi
	cp -r the_alchemiser "$(ARTIFACTS_DIR)/"
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Coordinator build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
