# Makefile for Data Quality Monitor Lambda Layer
# Downloads pre-built awswrangler layer and adds yfinance for external data validation
#
# awswrangler layer provides: pandas, numpy, pyarrow, boto3, botocore, pydantic, requests, etc.
# We add: yfinance and its dependencies
#
# Total size: ~190MB unzipped (well under 250MB Lambda limit)

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

	# Add yfinance and its dependencies
	@echo "➕ Adding yfinance..."
	$(PIP) install -q \
		yfinance==$(YFINANCE_VERSION) \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade

	# Add Data Quality Monitor-specific deps not in awswrangler
	@echo "➕ Adding Data Quality Monitor-specific dependencies..."
	$(PIP) install -q \
		pydantic \
		pydantic-settings \
		structlog \
		dependency-injector \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade

	# Cleanup
	rm -f /tmp/awswrangler-layer.zip

	@echo "✅ Data Quality Monitor layer build complete"
	@du -sh "$(ARTIFACTS_DIR)/python" 2>/dev/null || du -sh "$(ARTIFACTS_DIR)" || true
