#!/bin/bash
set -e

# Deploy WeasyPrint Lambda Layer from kotify/cloud-print-utils
# This script downloads the pre-built layer and publishes it to your AWS account

WEASYPRINT_VERSION="66.0"
PYTHON_VERSION="3.12"
ARCH="x86_64"
REGION="${AWS_REGION:-us-east-1}"
LAYER_NAME="weasyprint-python312"

DOWNLOAD_URL="https://github.com/kotify/cloud-print-utils/releases/download/weasyprint-${WEASYPRINT_VERSION}/weasyprint-layer-python${PYTHON_VERSION}-${ARCH}.zip"
ZIP_FILE="weasyprint-layer-python${PYTHON_VERSION}-${ARCH}.zip"

echo "🔍 Downloading WeasyPrint layer from kotify/cloud-print-utils..."
echo "   URL: ${DOWNLOAD_URL}"

# Download the layer zip
curl -L -o "${ZIP_FILE}" "${DOWNLOAD_URL}"

echo "✅ Downloaded: ${ZIP_FILE}"
echo ""
echo "📦 Publishing layer to AWS Lambda..."
echo "   Region: ${REGION}"
echo "   Layer Name: ${LAYER_NAME}"

# Publish the layer
LAYER_VERSION=$(aws lambda publish-layer-version \
    --region "${REGION}" \
    --layer-name "${LAYER_NAME}" \
    --description "WeasyPrint ${WEASYPRINT_VERSION} for Python ${PYTHON_VERSION} (from kotify/cloud-print-utils)" \
    --license-info "BSD-3-Clause" \
    --compatible-runtimes "python${PYTHON_VERSION}" \
    --compatible-architectures "${ARCH}" \
    --zip-file "fileb://${ZIP_FILE}" \
    --query 'Version' \
    --output text)

echo "✅ Layer published successfully!"
echo ""
echo "📋 Layer Details:"
echo "   Layer Name: ${LAYER_NAME}"
echo "   Version: ${LAYER_VERSION}"
echo "   ARN: arn:aws:lambda:${REGION}:$(aws sts get-caller-identity --query Account --output text):layer:${LAYER_NAME}:${LAYER_VERSION}"
echo ""
echo "🎯 Add this ARN to your template.yaml ReportGeneratorFunction Layers section"
echo ""

# Clean up
rm -f "${ZIP_FILE}"
echo "🧹 Cleaned up downloaded zip file"
