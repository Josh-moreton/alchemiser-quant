#!/usr/bin/env python3
"""
Test Runner for Alpaca Trading Bot Test Suite
Provides convenient commands to run different test categories
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_command(cmd, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False


def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking test dependencies...")
    
    required_packages = ['pytest', 'pytest-mock', 'pytest-cov']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        install_cmd = f"pip install {' '.join(missing_packages)}"
        success = run_command(install_cmd, f"Installing {', '.join(missing_packages)}")
        if not success:
            print("❌ Failed to install dependencies")
            return False
    
    print("✅ All dependencies are available")
    return True


def run_unit_tests():
    """Run unit tests only"""
    cmd = "python -m pytest tests/test_alpaca_trading_bot.py -v --tb=short -m 'not slow'"
    return run_command(cmd, "Running Unit Tests")


def run_integration_tests():
    """Run integration tests"""
    cmd = "python -m pytest tests/test_alpaca_trading_bot.py::TestIntegrationScenarios -v --tb=short"
    return run_command(cmd, "Running Integration Tests")


def run_market_scenario_tests():
    """Run market scenario tests"""
    cmd = "python -m pytest tests/test_market_scenarios.py -v --tb=short"
    return run_command(cmd, "Running Market Scenario Tests")


def run_performance_tests():
    """Run performance tests"""
    cmd = "python -m pytest tests/test_performance.py -v --tb=short -m 'not slow'"
    return run_command(cmd, "Running Performance Tests")


def run_all_tests():
    """Run all tests"""
    cmd = "python -m pytest tests/ -v --tb=short --durations=10"
    return run_command(cmd, "Running All Tests")


def run_coverage_report():
    """Run tests with coverage report"""
    cmd = "python -m pytest tests/ --cov=src/execution --cov-report=html --cov-report=term-missing"
    return run_command(cmd, "Running Tests with Coverage Report")


def run_fast_tests():
    """Run only fast tests (no performance/slow tests)"""
    cmd = "python -m pytest tests/ -v --tb=short -m 'not slow and not performance'"
    return run_command(cmd, "Running Fast Tests Only")


def run_specific_test(test_name):
    """Run a specific test or test class"""
    cmd = f"python -m pytest tests/ -v --tb=short -k '{test_name}'"
    return run_command(cmd, f"Running Specific Test: {test_name}")


def validate_bot_setup():
    """Validate that the bot can be imported and basic setup works"""
    print("\n🔧 Validating Alpaca Bot Setup...")
    
    try:
        # Test imports
        from execution.alpaca_trader import AlpacaTradingBot
        print("✅ AlpacaTradingBot import successful")
        
        # Test mock initialization
        from unittest.mock import patch
        import os
        
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    bot = AlpacaTradingBot(paper_trading=True)
                    print("✅ Mock bot initialization successful")
        
        print("✅ Bot setup validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Bot setup validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n📊 Generating Comprehensive Test Report...")
    
    # Create reports directory
    reports_dir = Path("test_reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Run tests with JUnit XML output
    cmd = f"python -m pytest tests/ --junitxml={reports_dir}/junit.xml --html={reports_dir}/report.html --self-contained-html"
    success = run_command(cmd, "Generating Test Report")
    
    if success:
        print(f"\n📋 Test reports generated in: {reports_dir.absolute()}")
        print(f"   - HTML Report: {reports_dir}/report.html")
        print(f"   - JUnit XML: {reports_dir}/junit.xml")
    
    return success


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Alpaca Trading Bot Test Runner")
    parser.add_argument('test_type', nargs='?', default='all', 
                       choices=['all', 'unit', 'integration', 'market', 'performance', 
                               'fast', 'coverage', 'validate', 'report'],
                       help='Type of tests to run')
    parser.add_argument('--specific', '-s', help='Run specific test by name')
    parser.add_argument('--no-deps', action='store_true', help='Skip dependency check')
    
    args = parser.parse_args()
    
    print("🚀 Alpaca Trading Bot Test Suite")
    print("=" * 60)
    
    # Check dependencies unless skipped
    if not args.no_deps:
        if not check_dependencies():
            print("❌ Dependency check failed. Use --no-deps to skip.")
            return False
    
    # Validate bot setup
    if not validate_bot_setup():
        print("❌ Bot setup validation failed.")
        return False
    
    # Run specific test if provided
    if args.specific:
        return run_specific_test(args.specific)
    
    # Run tests based on type
    test_functions = {
        'all': run_all_tests,
        'unit': run_unit_tests,
        'integration': run_integration_tests,
        'market': run_market_scenario_tests,
        'performance': run_performance_tests,
        'fast': run_fast_tests,
        'coverage': run_coverage_report,
        'validate': lambda: True,  # Already validated above
        'report': generate_test_report
    }
    
    success = test_functions[args.test_type]()
    
    if success:
        print(f"\n✅ {args.test_type.title()} tests completed successfully!")
    else:
        print(f"\n❌ {args.test_type.title()} tests failed!")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
