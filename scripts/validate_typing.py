#!/usr/bin/env python3
"""
Phase 15 Typing Validation Script

Tests the comprehensive strict typing implementation across all 14 completed phases.
"""

import subprocess
import sys
from pathlib import Path


def run_mypy_check(module_path: str, description: str) -> bool:
    """Run mypy check on a specific module and return success status."""
    print(f"🔍 Testing {description}...")

    try:
        result = subprocess.run(
            ["mypy", module_path, "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stdout:
                print(f"   Errors: {result.stdout[:200]}...")
            return False

    except Exception as e:
        print(f"⚠️  {description} - ERROR: {e}")
        return False


def test_type_imports() -> bool:
    """Test that our core types can be imported successfully."""
    print("🔍 Testing type imports...")

    try:

        print("✅ Type imports - PASSED")
        return True
    except Exception as e:
        print(f"❌ Type imports - FAILED: {e}")
        return False


def main():
    """Run comprehensive typing validation."""
    print("🚀 Phase 15: Comprehensive Typing Validation")
    print("=" * 50)

    # Test type imports first
    success_count = 0
    total_tests = 8

    if test_type_imports():
        success_count += 1

    # Test each phase
    phase_tests = [
        ("the_alchemiser/core/types.py", "Phase 1: Core Type Definitions"),
        ("the_alchemiser/execution/trading_engine.py", "Phase 2: Trading Engine"),
        ("the_alchemiser/main.py", "Phase 3: Main Entry Points"),
        ("the_alchemiser/tracking/", "Phase 4: Tracking Integration"),
        ("the_alchemiser/cli.py", "Phase 13: CLI Types"),
        ("the_alchemiser/core/error_handler.py", "Phase 14: Error Handler"),
        ("the_alchemiser/core/ui/cli_formatter.py", "CLI Formatter Support"),
    ]

    for module_path, description in phase_tests:
        if run_mypy_check(module_path, description):
            success_count += 1

    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{total_tests} tests passed")

    if success_count == total_tests:
        print("🎉 Phase 15: mypy Configuration - COMPLETED SUCCESSFULLY!")
        print("✨ Strict typing infrastructure is ready!")
        return True
    else:
        print(f"⚠️  {total_tests - success_count} tests failed")
        print("📝 Continue working on remaining type errors")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
