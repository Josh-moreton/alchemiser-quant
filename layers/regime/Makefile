# Regime Layer Build
# Builds the Lambda layer with hmmlearn and dependencies

LAYER_NAME := regime
PYTHON_VERSION := 3.12

.PHONY: build clean

build:
	@echo "Building $(LAYER_NAME) layer..."
	rm -rf python
	mkdir -p python
	pip install --upgrade pip
	pip install \
		--target python \
		--platform manylinux2014_x86_64 \
		--implementation cp \
		--python-version $(PYTHON_VERSION) \
		--only-binary=:all: \
		-r requirements.txt
	@echo "Layer built successfully"
	@du -sh python

clean:
	rm -rf python
