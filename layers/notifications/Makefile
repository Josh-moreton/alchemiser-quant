# Makefile for Notifications Lambda Layer
# Provides: pydantic, structlog, alpaca-py (for account info queries)

PYTHON_VERSION := 3.12

# Use python3 -m pip for portability across environments
PIP := python3 -m pip

.PHONY: build-NotificationsLayer

build-NotificationsLayer:
	@echo "📦 Building Notifications Layer..."
	@echo "   Target: $(ARTIFACTS_DIR)"
	
	# Install all dependencies from requirements.txt
	@echo "➕ Installing dependencies..."
	$(PIP) install -q \
		-r requirements.txt \
		-t "$(ARTIFACTS_DIR)/python" \
		--upgrade
	
	@echo "✅ Notifications layer build complete"
	@du -sh "$(ARTIFACTS_DIR)/python" 2>/dev/null || du -sh "$(ARTIFACTS_DIR)" || true
