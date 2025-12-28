# SharedCodeLayer Build
# Copies the_alchemiser/shared/ from source repository
# SAM calls this during layer build

ARTIFACTS_DIR ?= $(shell pwd)
SOURCE_DIR := $(if $(CODEBUILD_SRC_DIR),$(CODEBUILD_SRC_DIR),$(shell cd ../.. 2>/dev/null && pwd || echo ""))

# Fallback source finding (same pattern as data_functions)
define find_source
$(if $(wildcard $(1)/the_alchemiser/__init__.py),$(1),)
endef

SOURCE_DIR := $(or \
	$(call find_source,$(SOURCE_DIR)), \
	$(call find_source,$(GITHUB_WORKSPACE)), \
	$(call find_source,$(shell pwd)/../..), \
	$(error Could not find source directory with the_alchemiser module))

.PHONY: build build-SharedCodeLayer

build-SharedCodeLayer: build

build:
	@echo "📦 Building SharedCodeLayer..."
	@echo "   Source: $(SOURCE_DIR)/the_alchemiser/shared"
	@echo "   Target: $(ARTIFACTS_DIR)/python"

	# Create package structure
	mkdir -p "$(ARTIFACTS_DIR)/python/the_alchemiser"

	# Copy shared module
	cp -r "$(SOURCE_DIR)/the_alchemiser/shared" "$(ARTIFACTS_DIR)/python/the_alchemiser/"
	cp "$(SOURCE_DIR)/the_alchemiser/__init__.py" "$(ARTIFACTS_DIR)/python/the_alchemiser/"
	cp "$(SOURCE_DIR)/the_alchemiser/py.typed" "$(ARTIFACTS_DIR)/python/the_alchemiser/" 2>/dev/null || true

	# Cleanup
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyo" -delete 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.md" -delete 2>/dev/null || true

	@echo "✅ SharedCodeLayer build complete"
	@du -sh "$(ARTIFACTS_DIR)/python/the_alchemiser/shared"
