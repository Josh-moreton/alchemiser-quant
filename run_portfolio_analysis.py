#!/usr/bin/env python3
"""
Portfolio Analysis Runner
Choose between quick analysis or comprehensive LSE screening.
"""

import subprocess
import sys
from datetime import datetime

def run_quick_analysis():
    """Run the quick portfolio optimizer."""
    print("Running Quick LSE Portfolio Analysis...")
    print("This will test ~50 curated LSE tickers and complete in a few minutes.")
    print("-" * 60)
    
    try:
        result = subprocess.run([sys.executable, "lse_portfolio_optimizer_quick.py"], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running quick analysis: {e}")
        return False

def run_comprehensive_analysis():
    """Run the comprehensive portfolio optimizer."""
    print("Running Comprehensive LSE Portfolio Analysis...")
    print("This will test 100+ LSE tickers and may take 30-60 minutes.")
    print("Consider running this overnight or during breaks.")
    print("-" * 60)
    
    try:
        result = subprocess.run([sys.executable, "lse_portfolio_optimizer.py"], 
                              capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running comprehensive analysis: {e}")
        return False

def main():
    print("LSE Portfolio Optimizer")
    print("=" * 50)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis tool finds optimal 2-3 stock portfolios with LQQ3 as core holding (66%)")
    print("Optimization target: Calmar ratio (CAGR / Max Drawdown)")
    print("\nChoose analysis type:")
    print("1. Quick Analysis (~5 minutes, curated tickers)")
    print("2. Comprehensive Analysis (30-60 minutes, all LSE tickers)")
    print("3. Exit")
    
    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            success = run_quick_analysis()
            if success:
                print("\n✓ Quick analysis completed successfully!")
                print("Check the generated CSV files for detailed results.")
            else:
                print("\n✗ Quick analysis failed.")
            break
            
        elif choice == "2":
            confirm = input("This will take a long time. Continue? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                success = run_comprehensive_analysis()
                if success:
                    print("\n✓ Comprehensive analysis completed successfully!")
                    print("Check the generated CSV files for detailed results.")
                else:
                    print("\n✗ Comprehensive analysis failed.")
            else:
                print("Comprehensive analysis cancelled.")
            break
            
        elif choice == "3":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
