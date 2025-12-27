# Data Lambda Function Build
# Uses Makefile to copy only necessary code (SAM's BuildProperties doesn't work reliably)

ARTIFACTS_DIR ?= $(shell pwd)
SOURCE_DIR := $(shell dirname $(shell dirname $(MAKEFILE_LIST)))

.PHONY: build build-SharedDataFunction build-DataQualityMonitorFunction

# SAM calls build-<FunctionName> for each function
build-SharedDataFunction: build
build-DataQualityMonitorFunction: build

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
	cp -r "$(SOURCE_DIR)/the_alchemiser/data_quality_monitor" "$(ARTIFACTS_DIR)/the_alchemiser/"
	cp -r "$(SOURCE_DIR)/the_alchemiser/config" "$(ARTIFACTS_DIR)/the_alchemiser/" 2>/dev/null || true
	
	# Cleanup Python cache
	find "$(ARTIFACTS_DIR)" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyc" -delete 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.pyo" -delete 2>/dev/null || true
	find "$(ARTIFACTS_DIR)" -type f -name "*.md" -delete 2>/dev/null || true
	
	@echo "✅ Data Lambda build complete"
	@du -sh "$(ARTIFACTS_DIR)/the_alchemiser"
