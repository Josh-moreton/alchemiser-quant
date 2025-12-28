# Data Lambda Build
# Copies data_v2 from source (includes strategy DSL files for symbol extraction)

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

.PHONY: build build-SharedDataFunction

build-SharedDataFunction: build

build:
	@echo "📦 Building Data Lambda..."
	mkdir -p "$(ARTIFACTS_DIR)/the_alchemiser"
	cp -r "$(SOURCE_DIR)/the_alchemiser/data_v2" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp "$(SOURCE_DIR)/the_alchemiser/__init__.py" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp "$(SOURCE_DIR)/the_alchemiser/py.typed" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	cp -r "$(SOURCE_DIR)/the_alchemiser/config" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	# Data also needs strategy DSL files for symbol extraction
	mkdir -p "$(ARTIFACTS_DIR)/the_alchemiser/strategy_v2"
	cp -r "$(SOURCE_DIR)/the_alchemiser/strategy_v2/strategies" "$(ARTIFACTS_DIR)/the_alchemiser/strategy_v2/" 2>/dev/null || true
	# Verify strategy DSL files exist (needed for symbol extraction)
	@if [ -d "$(ARTIFACTS_DIR)/the_alchemiser/strategy_v2/strategies" ]; then \
		CLJ_COUNT=$$(find "$(ARTIFACTS_DIR)/the_alchemiser/strategy_v2/strategies" -name "*.clj" 2>/dev/null | wc -l | tr -d ' '); \
		echo "   Found $$CLJ_COUNT .clj strategy files for symbol extraction"; \
	fi
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Data build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
