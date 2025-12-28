# TradeAggregator Lambda Build
# Copies trade_aggregator from source

ARTIFACTS_DIR ?= $(shell pwd)
SOURCE_DIR := $(if $(CODEBUILD_SRC_DIR),$(CODEBUILD_SRC_DIR),$(shell cd ../.. 2>/dev/null && pwd || echo ""))

define find_source
$(if $(wildcard $(1)/the_alchemiser/__init__.py),$(1),)
endef

SOURCE_DIR := $(or \
	$(call find_source,$(SOURCE_DIR)), \
	$(call find_source,$(GITHUB_WORKSPACE)), \
	$(call find_source,$(shell pwd)/../..), \
	$(error Could not find source directory with the_alchemiser module))

.PHONY: build build-TradeAggregatorFunction

build-TradeAggregatorFunction: build

build:
	@echo "📦 Building TradeAggregator Lambda..."
	mkdir -p "$(ARTIFACTS_DIR)/the_alchemiser"
	cp -r "$(SOURCE_DIR)/the_alchemiser/trade_aggregator" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp "$(SOURCE_DIR)/the_alchemiser/__init__.py" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp "$(SOURCE_DIR)/the_alchemiser/py.typed" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	cp -r "$(SOURCE_DIR)/the_alchemiser/config" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ TradeAggregator build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
