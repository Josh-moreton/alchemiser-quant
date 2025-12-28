# Strategy Lambda Build
# Code is synced from source via root Makefile before SAM build

ARTIFACTS_DIR ?= $(shell pwd)

.PHONY: build build-StrategyFunction

build-StrategyFunction: build

build:
	@echo "📦 Building Strategy Lambda..."
	if [ ! -d "the_alchemiser/strategy_v2" ]; then \
		echo "❌ ERROR: strategy_v2 not found. Run 'make sync-all' from repo root first."; \
		exit 1; \
	fi
	# Verify .clj files exist
	@CLJ_COUNT=$$(find the_alchemiser/strategy_v2 -name "*.clj" 2>/dev/null | wc -l | tr -d ' '); \
	echo "   Found $$CLJ_COUNT .clj strategy files"; \
	[ $$CLJ_COUNT -gt 0 ] || (echo "⚠️  WARNING: No .clj files found!" && exit 1)
	cp -r the_alchemiser "$(ARTIFACTS_DIR)/"
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Strategy build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
