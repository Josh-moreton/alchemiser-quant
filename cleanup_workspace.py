#!/usr/bin/env python3
"""
Workspace Cleanup Script
Organize files for LQQ3 desktop app deployment
"""

import os
import shutil
from pathlib import Path

def organize_workspace():
    """Organize workspace into production app and archive folders"""
    
    print("🧹 Organizing LQQ3 workspace...")
    
    # Create directories
    os.makedirs('archive', exist_ok=True)
    os.makedirs('desktop_app', exist_ok=True)
    os.makedirs('analysis_reports', exist_ok=True)
    
    # Core files needed for desktop app
    core_files = [
        'lqq3_signal_app.py',           # Main desktop app
        'requirements.txt',              # Dependencies
        'README.md'                      # Documentation
    ]
    
    # Analysis and documentation files to keep
    analysis_files = [
        'LADDERING_ANALYSIS_SUMMARY.md',
        'VARIABLE_ALLOCATION_ANALYSIS.md', 
        'COMBINED_SIGNAL_GUIDE.md',
        'HYBRID_STRATEGY_ANALYSIS.md',
        'SIGNAL_NOISE_ANALYSIS.md'
    ]
    
    # Archive all CSV results and old scripts
    archive_patterns = [
        '*.csv',
        '*_results.csv',
        '*comparison*.py',
        '*analysis*.py',
        '*testing*.py',
        '*backtest*.py',
        'analyze_*.py',
        'create_*.py',
        'debug_*.py',
        'check_*.py',
        'run_*.py',
        'ultimate_*.py',
        'optimal_*.py',
        'hybrid_*.py',
        'macd_vs_*.py',
        'combined_*.py',
        'final_*.py',
        'variable_allocation_*.py',
        'laddering_*.py',
        'risk_*.py',
        'trading_strategy_*.py',
        'advanced_*.py',
        'optimized_*.py',
        'quick_signal_check.py',        # Old version
        '*.html',
        '*.png'
    ]
    
    # Copy core files to desktop_app
    print("\n📱 Setting up desktop app...")
    for file in core_files:
        if os.path.exists(file):
            shutil.copy2(file, f'desktop_app/{file}')
            print(f"   ✓ {file}")
    
    # Move analysis files to reports folder
    print("\n📊 Organizing analysis reports...")
    for file in analysis_files:
        if os.path.exists(file):
            shutil.move(file, f'analysis_reports/{file}')
            print(f"   ✓ {file}")
    
    # Archive old files
    print("\n📦 Archiving old files...")
    archived_count = 0
    
    for pattern in archive_patterns:
        import glob
        for file in glob.glob(pattern):
            if os.path.isfile(file):
                shutil.move(file, f'archive/{file}')
                archived_count += 1
    
    print(f"   ✓ Archived {archived_count} files")
    
    # Clean up __pycache__
    if os.path.exists('__pycache__'):
        shutil.rmtree('__pycache__')
        print("   ✓ Removed __pycache__")
    
    print("\n📁 Final structure:")
    print("   desktop_app/          - Production app files")
    print("   analysis_reports/     - Documentation and analysis")
    print("   archive/              - Historical files and experiments")
    print("   .venv/                - Python environment")
    print("   .git/                 - Git repository")

def create_app_readme():
    """Create README for desktop app"""
    readme_content = """# LQQ3 Trading Signal Desktop App

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run daily signal check:**
   ```bash
   python lqq3_signal_app.py
   ```

## Strategy Overview

**Binary Exit with Laddered Entry** - Optimal risk-adjusted allocation:

- **0 bullish signals** → 33% LQQ3, 67% Cash (Defensive)
- **1 bullish signal** → 66% LQQ3, 34% Cash (Balanced) 
- **2 bullish signals** → 100% LQQ3, 0% Cash (Aggressive)

## Signals

1. **MACD (12,26,9)**: Momentum indicator
   - Bullish when MACD line > Signal line
   - Fast-responding, catches early moves

2. **200-day SMA**: Trend indicator  
   - Bullish when TQQQ price > 200-day average
   - Slow-responding, confirms major trends

## Usage

Run the app daily before market open to get:
- Current signal status
- Recommended portfolio allocation  
- Signal changes from previous day
- Key levels to watch

## Performance

Historical results (2012-2025):
- **6,187% total returns** vs 5,405% buy-and-hold
- **1.15 Sharpe ratio** (excellent risk-adjusted returns)
- **-44% maximum drawdown** (vs -60% for binary allocation)
- **22 trades per year** (reasonable frequency)

## Files

- `lqq3_signal_app.py` - Main application
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

---

*Based on 12+ years of backtesting. Past performance does not guarantee future results.*
"""
    
    with open('desktop_app/README.md', 'w') as f:
        f.write(readme_content)
    
    print("✓ Created desktop app README.md")

def create_requirements():
    """Create clean requirements.txt for desktop app"""
    requirements = """# LQQ3 Trading Signal App Dependencies
yfinance>=0.2.18
pandas>=2.0.0
numpy>=1.24.0
"""
    
    with open('desktop_app/requirements.txt', 'w') as f:
        f.write(requirements)
    
    print("✓ Created desktop app requirements.txt")

def main():
    """Main cleanup function"""
    print("🚀 LQQ3 Workspace Cleanup & Desktop App Setup")
    print("=" * 50)
    
    organize_workspace()
    create_app_readme()
    create_requirements()
    
    print("\n✅ Cleanup complete!")
    print("\n📱 Your desktop app is ready in: ./desktop_app/")
    print("📊 Analysis reports are in: ./analysis_reports/")
    print("📦 Archived files are in: ./archive/")
    
    print("\n🎯 To use your desktop app:")
    print("   cd desktop_app")
    print("   pip install -r requirements.txt")
    print("   python lqq3_signal_app.py")

if __name__ == "__main__":
    main()
