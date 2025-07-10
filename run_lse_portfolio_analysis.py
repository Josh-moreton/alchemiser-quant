#!/usr/bin/env python3
"""
LSE Portfolio Optimizer Runner
Choose the scope of analysis: quick test, medium, or full analysis
"""

import subprocess
import sys
import os
from datetime import datetime

def run_quick_test():
    """Run with just 100 tickers for quick testing."""
    print("Running QUICK TEST with ~100 tickers (5-10 minutes)")
    print("This will test a subset for quick validation.")
    print("-" * 60)
    
    # Modify the script to use limited tickers
    cmd = [sys.executable, "-c", """
import sys
sys.path.insert(0, '.')
from lse_portfolio_optimizer_csv import *

# Override the batch sizes for quick test
BATCH_SIZE = 50
MAX_WORKERS = 8

# Limit tickers for quick test
def load_lse_tickers_limited(csv_file="All_LSE.csv"):
    tickers, ticker_info = load_lse_tickers(csv_file)
    # Take first 100 tickers for quick test
    limited_tickers = tickers[:100]
    limited_info = {k: v for k, v in ticker_info.items() if k in limited_tickers}
    print(f"Quick test: Limited to {len(limited_tickers)} tickers")
    return limited_tickers, limited_info

# Override the function
import lse_portfolio_optimizer_csv
lse_portfolio_optimizer_csv.load_lse_tickers = load_lse_tickers_limited

# Run the main function
main()
"""]
    
    try:
        result = subprocess.run(cmd, cwd="/Users/joshua.moreton/Documents/GitHub/LQQ3")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_medium_analysis():
    """Run with shares and major ETFs only."""
    print("Running MEDIUM ANALYSIS with shares and major ETFs (30-60 minutes)")
    print("This focuses on stocks and ETFs, excluding bonds and complex instruments.")
    print("-" * 80)
    
    # Modify to include only shares and ETFs
    cmd = [sys.executable, "-c", """
import sys
sys.path.insert(0, '.')
from lse_portfolio_optimizer_csv import *

# Override asset types for medium analysis
INCLUDE_ASSET_TYPES = ['SHRS', 'ETFS']  # Only shares and ETFs

# Import and override
import lse_portfolio_optimizer_csv
lse_portfolio_optimizer_csv.INCLUDE_ASSET_TYPES = INCLUDE_ASSET_TYPES

main()
"""]
    
    try:
        result = subprocess.run(cmd, cwd="/Users/joshua.moreton/Documents/GitHub/LQQ3")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_full_analysis():
    """Run the complete analysis with all asset types."""
    print("Running FULL ANALYSIS with all LSE instruments (5-10 minutes with cache)")
    print("This tests ALL eligible instruments: shares, ETFs, ETCs, and other equity-like instruments.")
    print("-" * 100)
    
    try:
        result = subprocess.run([sys.executable, "lse_portfolio_optimizer_csv.py"], 
                              cwd="/Users/joshua.moreton/Documents/GitHub/LQQ3")
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 80)
    print("LSE PORTFOLIO OPTIMIZER")
    print("Find optimal 2-3 stock portfolios with LQQ3 as 66% core holding")
    print("=" * 80)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nAnalysis Options:")
    print("1. Quick Test (~100 tickers, 2-3 minutes with cache)")
    print("2. Medium Analysis (Shares & ETFs only, 5-10 minutes with cache)")  
    print("3. Full Analysis (All LSE instruments, 5-10 minutes with cache)")
    print("4. Download/Update Data Cache (60-120 minutes)")
    print("5. Exit")
    
    while True:
        choice = input(f"\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            print("\n" + "="*60)
            success = run_quick_test()
            if success:
                print("\n✓ Quick test completed successfully!")
            else:
                print("\n✗ Quick test failed.")
            break
            
        elif choice == "2":
            confirm = input("Medium analysis will take 5-10 minutes with cache. Continue? (Y/n): ").strip().lower()
            if confirm != 'n':
                print("\n" + "="*80)
                success = run_medium_analysis()
                if success:
                    print("\n✓ Medium analysis completed successfully!")
                else:
                    print("\n✗ Medium analysis failed.")
            else:
                print("Medium analysis cancelled.")
            break
            
        elif choice == "3":
            confirm = input("Full analysis will take 5-10 minutes with cache. Continue? (Y/n): ").strip().lower()
            if confirm != 'n':
                print("\n" + "="*100)
                success = run_full_analysis()
                if success:
                    print("\n✓ Full analysis completed successfully!")
                else:
                    print("\n✗ Full analysis failed.")
            else:
                print("Full analysis cancelled.")
            break
            
        elif choice == "4":
            print("\n" + "="*80)
            print("DOWNLOADING AND CACHING DATA")
            print("="*80)
            print("This will download all LSE ticker data and cache it locally.")
            print("This only needs to be done once (or when you want to refresh data).")
            confirm = input("This will take 60-120 minutes. Continue? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                try:
                    result = subprocess.run([sys.executable, "lse_data_downloader.py"], 
                                          cwd="/Users/joshua.moreton/Documents/GitHub/LQQ3")
                    if result.returncode == 0:
                        print("\n✓ Data caching completed successfully!")
                        print("You can now run fast analysis (options 1-3).")
                    else:
                        print("\n✗ Data caching failed.")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Data caching cancelled.")
            break
            
        elif choice == "5":
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
    
    print("\nResults will be saved as CSV files with timestamp.")
    print("Check for files like: lse_2stock_portfolio_results_YYYYMMDD_HHMMSS.csv")

if __name__ == "__main__":
    main()
