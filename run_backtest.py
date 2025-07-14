#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Backtest Launcher
Runs comprehensive backtesting from the correct directory
"""

import subprocess
import sys
import os

def main():
    print("🚀 NUCLEAR TRADING STRATEGY - BACKTEST MODE")
    print("=" * 60)
    print("Running comprehensive backtest...")
    print()
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'main.py')
    
    try:
        # Run the main script in backtest mode
        result = subprocess.run([sys.executable, main_script, 'backtest', '--backtest-type', 'comprehensive'], 
                              cwd=script_dir)
        
        if result.returncode == 0:
            print(f"\n✅ Backtest completed successfully!")
        else:
            print(f"\n❌ Backtest failed with return code: {result.returncode}")
            
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"\n❌ Error launching backtest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
