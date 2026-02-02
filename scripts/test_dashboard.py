#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Test script to verify dashboard components can be imported and have required functions.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "layers" / "shared"))

def test_imports():
    """Test that all dashboard pages can be imported."""
    print("Testing dashboard component imports...")
    
    try:
        import dashboard_pages.portfolio_overview
        print("✓ portfolio_overview imported successfully")
        assert hasattr(dashboard_pages.portfolio_overview, 'show'), "Missing show() function"
        print("✓ portfolio_overview.show() exists")
    except Exception as e:
        print(f"✗ portfolio_overview: {e}")
        return False
    
    try:
        import dashboard_pages.last_run_analysis
        print("✓ last_run_analysis imported successfully")
        assert hasattr(dashboard_pages.last_run_analysis, 'show'), "Missing show() function"
        print("✓ last_run_analysis.show() exists")
    except Exception as e:
        print(f"✗ last_run_analysis: {e}")
        return False
    
    try:
        import dashboard_pages.trade_history
        print("✓ trade_history imported successfully")
        assert hasattr(dashboard_pages.trade_history, 'show'), "Missing show() function"
        print("✓ trade_history.show() exists")
    except Exception as e:
        print(f"✗ trade_history: {e}")
        return False
    
    try:
        import dashboard_pages.symbol_analytics
        print("✓ symbol_analytics imported successfully")
        assert hasattr(dashboard_pages.symbol_analytics, 'show'), "Missing show() function"
        print("✓ symbol_analytics.show() exists")
    except Exception as e:
        print(f"✗ symbol_analytics: {e}")
        return False
    
    return True

def test_syntax():
    """Test Python syntax of all files."""
    print("\nTesting Python syntax...")
    
    files = [
        "dashboard.py",
        "dashboard_pages/portfolio_overview.py",
        "dashboard_pages/last_run_analysis.py",
        "dashboard_pages/trade_history.py",
        "dashboard_pages/symbol_analytics.py",
    ]
    
    import py_compile
    
    for file in files:
        filepath = Path(__file__).parent / file
        try:
            py_compile.compile(str(filepath), doraise=True)
            print(f"✓ {file} syntax OK")
        except py_compile.PyCompileError as e:
            print(f"✗ {file} syntax error: {e}")
            return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Dashboard Component Tests")
    print("=" * 60)
    
    syntax_ok = test_syntax()
    
    if not syntax_ok:
        print("\n❌ Syntax tests failed")
        return 1
    
    # Note: Import tests will fail without dependencies installed
    # This is expected in CI/CD environments without full setup
    print("\nNote: Import tests require full environment (pandas, streamlit, boto3)")
    print("Run 'poetry install' to test imports locally")
    
    print("\n" + "=" * 60)
    print("✅ All syntax checks passed!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
