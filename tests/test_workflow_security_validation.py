#!/usr/bin/env python3
"""
Tests for workflow security validation script.
Tests various workflow scenarios to ensure proper security validation.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add parent directory to path to import the validator
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from validate_workflow_security import validate_workflow_file, validate_all_workflows


def test_safe_workflow():
    """Test that safe workflows pass validation."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Safe CI
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "Safe"
""")
        f.flush()
        path = Path(f.name)
    
    try:
        violations = validate_workflow_file(path)
        assert len(violations) == 0, f"Expected no violations but got: {violations}"
        print("✅ Test passed: Safe workflow with push trigger")
    finally:
        path.unlink()


def test_pull_request_target_violation():
    """Test that pull_request_target triggers are blocked."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Malicious
on:
  pull_request_target:
jobs:
  steal:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ secrets.API_KEY }}"
""")
        f.flush()
        path = Path(f.name)
    
    try:
        violations = validate_workflow_file(path)
        assert len(violations) == 1, f"Expected 1 violation but got {len(violations)}"
        assert "CRITICAL" in violations[0], "Expected CRITICAL severity"
        assert "pull_request_target" in violations[0], "Expected pull_request_target mention"
        print("✅ Test passed: pull_request_target blocked with CRITICAL")
    finally:
        path.unlink()


def test_pull_request_with_secrets_warning():
    """Test that pull_request with secrets generates a warning."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Risky PR
on:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ secrets.API_KEY }}"
""")
        f.flush()
        path = Path(f.name)
    
    try:
        violations = validate_workflow_file(path)
        assert len(violations) == 1, f"Expected 1 violation but got {len(violations)}"
        assert "WARNING" in violations[0], "Expected WARNING severity"
        assert "pull_request" in violations[0], "Expected pull_request mention"
        print("✅ Test passed: pull_request with secrets warned")
    finally:
        path.unlink()


def test_pull_request_without_secrets_safe():
    """Test that pull_request without secrets is allowed."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Safe PR Check
on:
  pull_request:
permissions:
  contents: read
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: make lint
""")
        f.flush()
        path = Path(f.name)
    
    try:
        violations = validate_workflow_file(path)
        assert len(violations) == 0, f"Expected no violations but got: {violations}"
        print("✅ Test passed: pull_request without secrets is safe")
    finally:
        path.unlink()


def test_workflow_dispatch_safe():
    """Test that workflow_dispatch is safe even with secrets."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Manual Deploy
on:
  workflow_dispatch:
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: echo "${{ secrets.DEPLOY_KEY }}"
""")
        f.flush()
        path = Path(f.name)
    
    try:
        violations = validate_workflow_file(path)
        assert len(violations) == 0, f"Expected no violations but got: {violations}"
        print("✅ Test passed: workflow_dispatch with secrets is safe")
    finally:
        path.unlink()


def test_multiple_triggers():
    """Test workflow with multiple triggers including dangerous ones."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("""
name: Mixed Triggers
on:
  push:
    branches: [main]
  pull_request_target:
  workflow_dispatch:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: echo "test"
""")
        f.flush()
        path = Path(f.name)
    
    try:
        violations = validate_workflow_file(path)
        assert len(violations) >= 1, f"Expected at least 1 violation but got {len(violations)}"
        assert any("pull_request_target" in v for v in violations), "Expected pull_request_target violation"
        print("✅ Test passed: Multiple triggers with pull_request_target caught")
    finally:
        path.unlink()


def run_all_tests():
    """Run all test cases."""
    print("🧪 Running workflow security validation tests...\n")
    
    tests = [
        test_safe_workflow,
        test_pull_request_target_violation,
        test_pull_request_with_secrets_warning,
        test_pull_request_without_secrets_safe,
        test_workflow_dispatch_safe,
        test_multiple_triggers,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {test.__name__}")
            print(f"   {e}")
            failed += 1
    
    print()
    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
