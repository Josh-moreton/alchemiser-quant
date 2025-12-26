# Makefile for Shared Data Lambda Layer
# Downloads pre-built awswrangler layer and adds alpaca-py + yfinance (without pandas duplication)
#
# awswrangler layer provides: pandas, numpy, pyarrow, boto3, botocore, pydantic, requests, etc.
# We add: alpaca-py, yfinance and their non-pandas dependencies
#
# Total size: ~200MB unzipped (under 250MB Lambda limit)

AWSWRANGLER_VERSION := 3.10.0
PYTHON_VERSION := 3.12
ALPACA_PY_VERSION := 0.43.0

# Use python3 -m pip for portability across environments
PIP := python3 -m pip

.PHONY: build-SharedDataLayer

build-SharedDataLayer:
	@echo "📦 Building Data Layer..."
	@echo "   awswrangler: $(AWSWRANGLER_VERSION)"
	@echo "   alpaca-py: $(ALPACA_PY_VERSION)"
	@echo "   Target: $(ARTIFACTS_DIR)"
	
	# Download pre-built awswrangler layer from AWS public bucket
	@echo "⬇️  Downloading awswrangler layer..."
	curl -sL "https://aws-data-wrangler-public-artifacts.s3.amazonaws.com/releases/$(AWSWRANGLER_VERSION)/awswrangler-layer-$(AWSWRANGLER_VERSION)-py$(PYTHON_VERSION).zip" -o /tmp/awswrangler-layer.zip
	
	# Extract to artifacts directory
	@echo "📂 Extracting awswrangler layer..."
	unzip -q -o /tmp/awswrangler-layer.zip -d "$(ARTIFACTS_DIR)"
	
	# Add alpaca-py WITHOUT its dependencies (pandas already in awswrangler)
	@echo "➕ Adding alpaca-py (no-deps)..."
	$(PIP) install -q \
		alpaca-py==$(ALPACA_PY_VERSION) \
		--no-deps \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade
	
	# Add alpaca-py's runtime dependencies that aren't in awswrangler
	@echo "➕ Adding alpaca-py runtime dependencies..."
	$(PIP) install -q \
		msgpack \
		sseclient-py \
		websockets \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade
	
	# Add Data-specific deps not in awswrangler
	@echo "➕ Adding Data-specific dependencies..."
	$(PIP) install -q \
		pydantic \
		pydantic-settings \
		structlog \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade
	
	# Add yfinance WITHOUT its dependencies (pandas already in awswrangler)
	@echo "➕ Adding yfinance (no-deps)..."
	$(PIP) install -q \
		yfinance \
		--no-deps \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade
	
	# Add yfinance's runtime dependencies not in awswrangler
	@echo "➕ Adding yfinance runtime dependencies..."
	$(PIP) install -q \
		lxml \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade
	
	# Cleanup
	rm -f /tmp/awswrangler-layer.zip
	
	@echo "✅ Data layer build complete"
	@du -sh "$(ARTIFACTS_DIR)/python" 2>/dev/null || du -sh "$(ARTIFACTS_DIR)" || true

