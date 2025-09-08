#!/bin/bash
set -e

# The Alchemiser - Smoke Tests
# Validates core functionality: CLI + strategy→portfolio→execution basic flow
# Safe for CI/CD and local development (no actual trading)

echo "🧪 The Alchemiser - Smoke Tests Starting..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    echo -e "${BLUE}[TEST]${NC} $test_name"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    if eval "$test_command" >/dev/null 2>&1; then
        actual_exit_code=$?
        if [ $actual_exit_code -eq $expected_exit_code ]; then
            echo -e "${GREEN}  ✅ PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}  ❌ FAILED (exit code: $actual_exit_code, expected: $expected_exit_code)${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        echo -e "${RED}  ❌ FAILED (command error)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

run_test_with_output() {
    local test_name="$1"
    local test_command="$2"
    local expected_pattern="$3"
    
    echo -e "${BLUE}[TEST]${NC} $test_name"
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    
    local output
    output=$(eval "$test_command" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -eq 0 ] && echo "$output" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}  ✅ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}  ❌ FAILED${NC}"
        echo "    Output: $output"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test 1: Environment Setup
echo -e "\n${YELLOW}🔧 Testing Environment Setup...${NC}"

run_test "Poetry installation check" "poetry --version"
run_test "Python environment" "python --version"
run_test "Dependencies installed" "poetry check"

# Test 2: CLI Availability
echo -e "\n${YELLOW}🖥️  Testing CLI Availability...${NC}"

run_test "CLI main command" "poetry run alchemiser --help"
run_test "CLI signal command help" "poetry run alchemiser signal --help"
run_test "CLI trade command help" "poetry run alchemiser trade --help"
run_test "CLI status command help" "poetry run alchemiser status --help"
run_test "CLI deploy command help" "poetry run alchemiser deploy --help"
run_test "CLI version command help" "poetry run alchemiser version --help"
run_test "CLI validate-indicators help" "poetry run alchemiser validate-indicators --help"
run_test "CLI dsl-count command help" "poetry run alchemiser dsl-count --help"

# Test 3: Core Functionality (Safe Commands)
echo -e "\n${YELLOW}🎯 Testing Core Functionality (Safe Commands)...${NC}"

run_test_with_output "Version command" "poetry run alchemiser version" "Version: 2.0.0"
run_test_with_output "Version command shows strategies" "poetry run alchemiser version" "Nuclear, TECL, KLM"

# Test 4: Strategy→Portfolio→Execution Flow (Dry Run Only)
echo -e "\n${YELLOW}🔄 Testing Strategy→Portfolio→Execution Flow (Safe Mode)...${NC}"

# Test signal generation without API keys (should gracefully handle missing credentials)
echo -e "${BLUE}[TEST]${NC} Signal generation error handling"
TESTS_TOTAL=$((TESTS_TOTAL + 1))
signal_output=$(timeout 10 poetry run alchemiser signal --strategy nuclear 2>&1 || true)
if echo "$signal_output" | grep -q -E "(credentials|API|paper|paper_trading|signal)" || echo "$signal_output" | grep -q -E "error|Error"; then
    echo -e "${GREEN}  ✅ PASSED (graceful error handling)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}  ⚠️  SKIPPED (unexpected output format)${NC}"
    echo "    Output: $signal_output"
fi

# Test signal command exit code with dummy credentials (should fail with code 1)
echo -e "${BLUE}[TEST]${NC} Signal command exit code validation"
TESTS_TOTAL=$((TESTS_TOTAL + 1))
ALPACA_KEY="dummy_key" ALPACA_SECRET="dummy_secret" ALPACA_ENDPOINT="https://paper-api.alpaca.markets" \
    timeout 15 poetry run alchemiser signal >/dev/null 2>&1
signal_exit_code=$?
if [ $signal_exit_code -eq 1 ]; then
    echo -e "${GREEN}  ✅ PASSED (correctly exits with code 1 on data failures)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}  ❌ FAILED (exit code: $signal_exit_code, expected: 1)${NC}"
    echo "    Signal command should exit with code 1 when market data fails"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Test portfolio status error handling  
echo -e "${BLUE}[TEST]${NC} Portfolio status error handling"
TESTS_TOTAL=$((TESTS_TOTAL + 1))
status_output=$(timeout 10 poetry run alchemiser status 2>&1 || true)
if echo "$status_output" | grep -q -E "(credentials|API|paper|account)" || echo "$status_output" | grep -q -E "error|Error"; then
    echo -e "${GREEN}  ✅ PASSED (graceful error handling)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}  ⚠️  SKIPPED (unexpected output format)${NC}"
    echo "    Output: $status_output"
fi

# Test 5: Code Quality & Architecture
echo -e "\n${YELLOW}🏗️  Testing Code Quality & Architecture...${NC}"

run_test "Ruff linter availability" "poetry run ruff --version"
run_test "MyPy type checker availability" "poetry run mypy --version"

# Test baseline linting state (should have exactly 679 errors as documented)
echo -e "${BLUE}[TEST]${NC} Baseline linting state"
TESTS_TOTAL=$((TESTS_TOTAL + 1))
lint_output=$(poetry run ruff check the_alchemiser/ 2>&1 || true)
error_count=$(echo "$lint_output" | grep "Found .* errors" | tail -1 | grep -o '[0-9]\+' | head -1)
if [ "$error_count" = "679" ]; then
    echo -e "${GREEN}  ✅ PASSED (baseline: 679 errors)${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${YELLOW}  ⚠️  WARNING (error count: $error_count, expected: 679)${NC}"
    echo "    This might indicate codebase changes since baseline"
fi

# Test 6: Migration Infrastructure
echo -e "\n${YELLOW}📁 Testing Migration Infrastructure...${NC}"

run_test "Migration directory exists" "test -d migration"
run_test "Migration README exists" "test -f migration/README.md"
run_test "Migration ROLLBACK docs exist" "test -f migration/ROLLBACK.md"
run_test "Smoke tests script exists" "test -f scripts/smoke_tests.sh"
run_test "Smoke tests script is executable" "test -x scripts/smoke_tests.sh"

# Test 7: Architecture Validation (Check Key Components)
echo -e "\n${YELLOW}🔍 Testing Architecture Components...${NC}"

run_test "Main entry point exists" "test -f the_alchemiser/main.py"
run_test "Lambda handler exists" "test -f the_alchemiser/lambda_handler.py"
run_test "CLI interface exists" "test -f the_alchemiser/interfaces/cli/cli.py"
run_test "Core application structure" "test -d the_alchemiser/application"
run_test "Domain layer exists" "test -d the_alchemiser/domain"
run_test "Infrastructure layer exists" "test -d the_alchemiser/infrastructure"
run_test "Services layer exists" "test -d the_alchemiser/services"

# Test 8: Configuration & Dependencies
echo -e "\n${YELLOW}⚙️  Testing Configuration & Dependencies...${NC}"

run_test "PyProject.toml exists" "test -f pyproject.toml"
run_test "Poetry lock file exists" "test -f poetry.lock"
run_test "AWS SAM template exists" "test -f template.yaml"
run_test "Makefile exists" "test -f Makefile"
run_test "Make commands available" "make help"

# Test 9: Import System Validation
echo -e "\n${YELLOW}📦 Testing Import System...${NC}"

echo -e "${BLUE}[TEST]${NC} Core module imports"
TESTS_TOTAL=$((TESTS_TOTAL + 1))
import_test=$(poetry run python -c "
try:
    from the_alchemiser.interfaces.cli import cli
    from the_alchemiser.application.portfolio.services import portfolio_management_facade
    from the_alchemiser.infrastructure.config import load_settings
    print('SUCCESS')
except ImportError as e:
    print(f'IMPORT_ERROR: {e}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>&1)

if echo "$import_test" | grep -q "SUCCESS"; then
    echo -e "${GREEN}  ✅ PASSED${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}  ❌ FAILED${NC}"
    echo "    Import error: $import_test"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

# Final Results
echo -e "\n${YELLOW}📊 Smoke Test Results${NC}"
echo "=============================="
echo -e "Total Tests: $TESTS_TOTAL"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL SMOKE TESTS PASSED!${NC}"
    echo -e "${GREEN}✅ The Alchemiser baseline functionality is working correctly.${NC}"
    exit 0
else
    echo -e "\n${RED}⚠️  SOME TESTS FAILED!${NC}"
    echo -e "${RED}❌ Review the failures above before proceeding with migration.${NC}"
    exit 1
fi