#!/bin/bash
# Test script for ephemeral stack name generation
# This validates the branch name sanitization logic used in the deploy workflow

echo "Testing Ephemeral Stack Name Generation"
echo "========================================"
echo ""

passed=0
failed=0

test_sanitization() {
    local input="$1"
    local expected="$2"
    
    # Apply same sanitization as workflow
    local sanitized=$(echo "$input" | tr '[:upper:]' '[:lower:]' | sed 's/[\/\._@]/-/g' | sed 's/[^a-z0-9-]//g' | cut -c1-40)
    sanitized=$(echo "$sanitized" | sed 's/^-*//' | sed 's/-*$//')
    
    if [ "$sanitized" = "$expected" ]; then
        echo "PASS: '$input' -> '$sanitized'"
        return 0
    else
        echo "FAIL: '$input' -> '$sanitized' (expected: '$expected')"
        return 1
    fi
}

# Run tests
if test_sanitization "feature/my-feature" "feature-my-feature"; then ((passed++)); else ((failed++)); fi
if test_sanitization "bugfix/fix_123" "bugfix-fix-123"; then ((passed++)); else ((failed++)); fi
if test_sanitization "FEAT/New.Feature" "feat-new-feature"; then ((passed++)); else ((failed++)); fi
if test_sanitization "test@branch" "test-branch"; then ((passed++)); else ((failed++)); fi
if test_sanitization "very/long/branch/name/that/needs/truncation" "very-long-branch-name-that-needs-truncat"; then ((passed++)); else ((failed++)); fi
if test_sanitization "feature/test_with.multiple@special/chars" "feature-test-with-multiple-special-chars"; then ((passed++)); else ((failed++)); fi
if test_sanitization "main" "main"; then ((passed++)); else ((failed++)); fi
if test_sanitization "production" "production"; then ((passed++)); else ((failed++)); fi
if test_sanitization "feature-already-clean" "feature-already-clean"; then ((passed++)); else ((failed++)); fi

echo ""
echo "========================================"
echo "Results: $passed passed, $failed failed"
echo ""

if [ $failed -gt 0 ]; then
    echo "Some tests failed!"
    exit 1
else
    echo "All tests passed!"
fi

echo ""
echo "Testing full stack name generation..."
echo "--------------------------------------"

# Test full stack name with short SHA
test_branch="feature/my-test"
test_sha="a1b2c3d"
stack_basename="alchemiser"

sanitized=$(echo "$test_branch" | tr '[:upper:]' '[:lower:]' | sed 's/[\/\._@]/-/g' | sed 's/[^a-z0-9-]//g' | cut -c1-40)
sanitized=$(echo "$sanitized" | sed 's/^-*//' | sed 's/-*$//')
stack_name="${stack_basename}-ephem-${sanitized}-${test_sha}"

echo "Branch: $test_branch"
echo "SHA: $test_sha"
echo "Stack name: $stack_name"
echo "Length: ${#stack_name} chars (limit: 128)"

if [ ${#stack_name} -le 128 ]; then
    echo "Stack name length OK"
else
    echo "Stack name too long!"
    exit 1
fi

echo ""
echo "All validation tests passed!"

