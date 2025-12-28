# Data Lambda Function Build
# Uses Makefile to copy only necessary code (SAM's BuildProperties doesn't work reliably)
#
# SAM workflow:
# 1. Copies CodeUri directory to temp build location
# 2. Runs make build-<FunctionName> with ARTIFACTS_DIR set
# 3. Packages contents of ARTIFACTS_DIR into Lambda zip
#
# We need to find the repo root relative to where SAM copied us

ARTIFACTS_DIR ?= $(shell pwd)

# SAM copies layers/data_functions/ to a temp dir and runs make there
# We need to find the repo root (../../ from layers/data_functions)
# But SAM also sets the working directory, so we use CODEBUILD_SRC_DIR or fallback
SOURCE_DIR := $(if $(CODEBUILD_SRC_DIR),$(CODEBUILD_SRC_DIR),$(shell cd ../.. 2>/dev/null && pwd || echo ""))

# Fallback: if we can't find source, check if the_alchemiser exists at common locations
define find_source
$(if $(wildcard $(1)/the_alchemiser/__init__.py),$(1),)
endef

# Try multiple locations
SOURCE_DIR := $(or \
	$(call find_source,$(SOURCE_DIR)), \
	$(call find_source,$(GITHUB_WORKSPACE)), \
	$(call find_source,$(shell pwd)/../..), \
	$(call find_source,/home/runner/work/alchemiser-quant/alchemiser-quant), \
	$(error Could not find source directory with the_alchemiser module))

.PHONY: build build-SharedDataFunction

# SAM calls build-<FunctionName> for each function
build-SharedDataFunction: build

build:
	@echo "📦 Building Data Lambda function code..."
	@echo "   Source: $(SOURCE_DIR)/the_alchemiser"
	@echo "   Target: $(ARTIFACTS_DIR)"
	
	# Create the_alchemiser package structure
	mkdir -p "$(ARTIFACTS_DIR)/the_alchemiser"
	
	# Copy only the modules needed for data lambdas
	cp -r "$(SOURCE_DIR)/the_alchemiser/__init__.py" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp -r "$(SOURCE_DIR)/the_alchemiser/py.typed" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	
	# Core modules needed
	cp -r "$(SOURCE_DIR)/the_alchemiser/shared" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp -r "$(SOURCE_DIR)/the_alchemiser/data_v2" "$(ARTIFACTS_DIR)/the_alchemiser/"

	# Config files and strategy DSL files (needed for symbol extraction)
	cp -r "$(SOURCE_DIR)/the_alchemiser/config" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	mkdir -p "$(ARTIFACTS_DIR)/the_alchemiser/strategy_v2"
	cp -r "$(SOURCE_DIR)/the_alchemiser/strategy_v2/strategies" "$(ARTIFACTS_DIR)/the_alchemiser/strategy_v2/" 2>/dev/null || true
	
	# Cleanup Python cache
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyo" -delete 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.md" -delete 2>/dev/null || true
	
	@echo "✅ Data Lambda build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
