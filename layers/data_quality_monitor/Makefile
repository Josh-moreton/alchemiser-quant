# Makefile for Data Quality Monitor Lambda Layer
# Downloads pre-built awswrangler layer and adds yfinance for external data validation
#
# awswrangler layer provides: pandas, numpy, pyarrow, boto3, botocore, pydantic, requests, etc.
# We add: yfinance (no-deps since pandas/numpy/requests already in awswrangler)
#
# Total size: ~200MB unzipped (within 250MB Lambda limit)

AWSWRANGLER_VERSION := 3.10.0
PYTHON_VERSION := 3.12
YFINANCE_VERSION := 0.2.49

# Use python3 -m pip for portability across environments
PIP := python3 -m pip

.PHONY: build-DataQualityMonitorLayer

build-DataQualityMonitorLayer:
	@echo "📦 Building Data Quality Monitor Layer..."
	@echo "   awswrangler: $(AWSWRANGLER_VERSION)"
	@echo "   yfinance: $(YFINANCE_VERSION)"
	@echo "   Target: $(ARTIFACTS_DIR)"

	# Download pre-built awswrangler layer from AWS public bucket
	@echo "⬇️  Downloading awswrangler layer..."
	curl -sL "https://aws-data-wrangler-public-artifacts.s3.amazonaws.com/releases/$(AWSWRANGLER_VERSION)/awswrangler-layer-$(AWSWRANGLER_VERSION)-py$(PYTHON_VERSION).zip" -o /tmp/awswrangler-layer.zip

	# Extract to artifacts directory
	@echo "📂 Extracting awswrangler layer..."
	unzip -q -o /tmp/awswrangler-layer.zip -d "$(ARTIFACTS_DIR)"

	# Add yfinance WITHOUT its heavy dependencies (pandas, numpy, requests already in awswrangler)
	@echo "➕ Adding yfinance (no-deps)..."
	$(PIP) install -q \
		yfinance==$(YFINANCE_VERSION) \
		--no-deps \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade

	# Add only the yfinance runtime dependencies not already in awswrangler
	# Skipping: pandas, numpy, pytz, requests (in awswrangler)
	# Skipping: curl_cffi, lxml (heavy, yfinance works without them - falls back to requests)
	@echo "➕ Adding yfinance runtime dependencies..."
	$(PIP) install -q \
		beautifulsoup4 \
		frozendict \
		multitasking \
		peewee \
		platformdirs \
		html5lib \
		--no-deps \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade

	# Add Data Quality Monitor-specific deps not in awswrangler
	# Note: awswrangler does NOT include pydantic, we must add it
	@echo "➕ Adding Data Quality Monitor-specific dependencies..."
	$(PIP) install -q \
		pydantic \
		pydantic-settings \
		structlog \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade

	# Cleanup to reduce size
	@echo "🧹 Cleaning up unnecessary files..."
	find "$(ARTIFACTS_DIR)/python" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)/python" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)/python" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
	find "$(ARTIFACTS_DIR)/python" -type f -name "*.pyc" -delete 2>/dev/null || true

	# Cleanup
	rm -f /tmp/awswrangler-layer.zip

	@echo "✅ Data Quality Monitor layer build complete"
	@du -sh "$(ARTIFACTS_DIR)/python" 2>/dev/null || du -sh "$(ARTIFACTS_DIR)" || true
