#!/bin/bash
# Test script to simulate the GitHub Actions migration validation locally

set -e

echo "🧪 Local Migration Validation Test"
echo "=================================="

# Set test environment
export PAPER_TRADING=true
export LOGGING__LEVEL=INFO
export PYTHONUNBUFFERED=1

echo ""
echo "🔧 Environment Check"
echo "-------------------"
poetry run python -c "import sys; print('Python:', sys.version.split()[0])"
poetry run python -c "import the_alchemiser; print('Alchemiser import: OK')"

echo ""
echo "🔍 MyPy Type Checking (Modular Structure)"
echo "----------------------------------------"
if poetry run mypy the_alchemiser/shared/ the_alchemiser/strategy/ the_alchemiser/portfolio/ the_alchemiser/execution/ --no-error-summary; then
    echo "✅ MyPy: PASSED"
    MYPY_STATUS="✅ PASSED"
else
    echo "⚠️ MyPy: WARNINGS (expected during migration)"
    MYPY_STATUS="⚠️ WARNINGS"
fi

echo ""
echo "🔍 Import Dependency Rules"
echo "-------------------------"
if poetry run lint-imports; then
    echo "✅ Import Rules: PASSED"
    IMPORT_STATUS="✅ PASSED"
else
    echo "❌ Import Rules: FAILED"
    IMPORT_STATUS="❌ FAILED"
    exit 1
fi

echo ""
echo "🧪 Smoke Tests"
echo "-------------"
if ./scripts/smoke_tests.sh > /dev/null 2>&1; then
    echo "✅ Smoke Tests: PASSED"
    SMOKE_STATUS="✅ PASSED"
else
    echo "⚠️ Smoke Tests: WARNINGS (may be expected during migration)"
    SMOKE_STATUS="⚠️ WARNINGS"
fi

echo ""
echo "📊 Migration Validation Summary"
echo "==============================="
echo "MyPy Type Checking: $MYPY_STATUS"
echo "Import Rules: $IMPORT_STATUS"
echo "Smoke Tests: $SMOKE_STATUS"
echo ""

if [ "$IMPORT_STATUS" = "✅ PASSED" ]; then
    echo "🎉 Core validation PASSED - Ready for PR!"
    exit 0
else
    echo "❌ Core validation FAILED - Fix import violations before PR"
    exit 1
fi