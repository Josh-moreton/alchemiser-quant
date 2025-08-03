#!/usr/bin/env python3
"""
Optimized Test Runner for The Alchemiser

This script provides different test execution modes:
- Fast unit tests (default)
- Integration tests  
- Slow tests (with timeout protection)
- Coverage analysis

Usage:
    python run_tests.py                    # Fast unit tests only
    python run_tests.py --all              # All tests except slow
    python run_tests.py --slow             # Include slow tests
    python run_tests.py --coverage         # Run with coverage
    python run_tests.py --parallel         # Run tests in parallel
    python run_tests.py --failed           # Re-run only failed tests
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle output."""
    print(f"\n🚀 {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print("Output:", result.stdout[-500:])  # Last 500 chars
        else:
            print(f"❌ {description} failed (exit code {result.returncode})")
            if result.stderr:
                print("Error:", result.stderr[-500:])
            return False
                
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"💥 {description} failed with exception: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Optimized test runner")
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    parser.add_argument('--fast', action='store_true', help='Run only fast unit tests')
    parser.add_argument('--slow', action='store_true', help='Run only slow tests')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--failed', action='store_true', help='Run only failed tests from last run')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--markers', type=str, help='Run tests with specific markers (e.g., "unit", "integration")')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Handle test selection
    if args.fast:
        cmd.extend(['-m', 'unit and not slow'])
    elif args.slow:
        cmd.extend(['-m', 'slow'])
    elif args.markers:
        cmd.extend(['-m', args.markers])
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(['--cov=the_alchemiser', '--cov-report=html', '--cov-report=term-missing'])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', 'auto'])
    
    # Add failed tests only
    if args.failed:
        cmd.append('--lf')
    
    # Add verbose output
    if args.verbose:
        cmd.append('-v')
    
    # Add tests directory
    cmd.append('tests/')
    
    # Execute the command
    success = run_command(cmd, "Running tests")
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
