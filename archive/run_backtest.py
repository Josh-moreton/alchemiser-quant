#!/usr/bin/env python3
"""
Quick start script for the LQQ3 trading strategy backtest
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def run_backtest():
    """Run the trading strategy backtest"""
    print("Starting LQQ3 trading strategy backtest...")
    try:
        # Import and run the backtest
        from trading_strategy_backtest import main
        backtester = main()
        return backtester
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please make sure all required packages are installed.")
        return None
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
        return None

if __name__ == "__main__":
    print("LQQ3 Trading Strategy Backtest")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Install packages
    if install_requirements():
        print("\n" + "=" * 50)
        # Run backtest
        backtester = run_backtest()
        
        if backtester:
            print("\n✅ Backtest completed successfully!")
            print("Check the generated plots and 'backtest_results.csv' file for detailed results.")
        else:
            print("❌ Backtest failed!")
    else:
        print("❌ Failed to install required packages!")
