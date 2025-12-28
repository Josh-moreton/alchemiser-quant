# Data Lambda Build
# Code is synced from source via root Makefile before SAM build

ARTIFACTS_DIR ?= $(shell pwd)

.PHONY: build build-SharedDataFunction

build-SharedDataFunction: build

build:
	@echo "📦 Building Data Lambda..."
	if [ ! -d "the_alchemiser/data_v2" ]; then \
		echo "❌ ERROR: data_v2 not found. Run 'make sync-all' from repo root first."; \
		exit 1; \
	fi
	# Verify strategy DSL files exist (needed for symbol extraction)
	@if [ -d "the_alchemiser/strategy_v2/strategies" ]; then \
		CLJ_COUNT=$$(find the_alchemiser/strategy_v2/strategies -name "*.clj" 2>/dev/null | wc -l | tr -d ' '); \
		echo "   Found $$CLJ_COUNT .clj strategy files for symbol extraction"; \
	fi
	cp -r the_alchemiser "$(ARTIFACTS_DIR)/"
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Data build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
