#!/usr/bin/env python3
"""Business Unit: dashboard | Status: current.

Test script to verify dashboard components can be imported and have required functions.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "layers" / "shared"))


def test_imports():
    """Test that all dashboard pages can be imported."""
    print("Testing dashboard component imports...")

    try:
        import pages.portfolio_overview
        print("  portfolio_overview imported successfully")
        assert hasattr(pages.portfolio_overview, "show"), "Missing show() function"
        print("  portfolio_overview.show() exists")
    except Exception as e:
        print(f"  FAIL portfolio_overview: {e}")
        return False

    try:
        import pages.last_run_analysis
        print("  last_run_analysis imported successfully")
        assert hasattr(pages.last_run_analysis, "show"), "Missing show() function"
        print("  last_run_analysis.show() exists")
    except Exception as e:
        print(f"  FAIL last_run_analysis: {e}")
        return False

    try:
        import pages.trade_history
        print("  trade_history imported successfully")
        assert hasattr(pages.trade_history, "show"), "Missing show() function"
        print("  trade_history.show() exists")
    except Exception as e:
        print(f"  FAIL trade_history: {e}")
        return False

    try:
        import pages.symbol_analytics
        print("  symbol_analytics imported successfully")
        assert hasattr(pages.symbol_analytics, "show"), "Missing show() function"
        print("  symbol_analytics.show() exists")
    except Exception as e:
        print(f"  FAIL symbol_analytics: {e}")
        return False

    try:
        import pages.strategy_performance
        print("  strategy_performance imported successfully")
        assert hasattr(pages.strategy_performance, "show"), "Missing show() function"
        print("  strategy_performance.show() exists")
    except Exception as e:
        print(f"  FAIL strategy_performance: {e}")
        return False

    try:
        import pages.execution_quality
        print("  execution_quality imported successfully")
        assert hasattr(pages.execution_quality, "show"), "Missing show() function"
        print("  execution_quality.show() exists")
    except Exception as e:
        print(f"  FAIL execution_quality: {e}")
        return False

    try:
        import pages.options_hedging
        print("  options_hedging imported successfully")
        assert hasattr(pages.options_hedging, "show"), "Missing show() function"
        print("  options_hedging.show() exists")
    except Exception as e:
        print(f"  FAIL options_hedging: {e}")
        return False

    return True


def test_syntax():
    """Test Python syntax of all files."""
    print("\nTesting Python syntax...")

    dashboard_root = Path(__file__).parent.parent

    files = [
        "app.py",
        "settings.py",
        "components/styles.py",
        "components/ui.py",
        "data/account.py",
        "data/strategy.py",
        "pages/portfolio_overview.py",
        "pages/forward_projection.py",
        "pages/last_run_analysis.py",
        "pages/trade_history.py",
        "pages/strategy_performance.py",
        "pages/execution_quality.py",
        "pages/symbol_analytics.py",
        "pages/options_hedging.py",
    ]

    import py_compile

    for file in files:
        filepath = dashboard_root / file
        try:
            py_compile.compile(str(filepath), doraise=True)
            print(f"  {file} syntax OK")
        except py_compile.PyCompileError as e:
            print(f"  FAIL {file} syntax error: {e}")
            return False

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Dashboard Component Tests")
    print("=" * 60)

    syntax_ok = test_syntax()

    if not syntax_ok:
        print("\nSyntax tests failed")
        return 1

    # Note: Import tests will fail without dependencies installed
    print("\nNote: Import tests require full environment (pandas, streamlit, boto3)")
    print("Run 'poetry install' to test imports locally")

    print("\n" + "=" * 60)
    print("All syntax checks passed!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
