#!/usr/bin/env python3
"""
LQQ3 Daily Signal Launcher
Simple one-click launcher for daily trading signals
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import yfinance
        import pandas
        import numpy
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    """Main launcher function"""
    print("🚀 LQQ3 Daily Signal Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("lqq3_signal_app.py"):
        print("❌ Error: lqq3_signal_app.py not found")
        print("   Please run this from the desktop_app directory")
        return False
    
    # Check dependencies
    if not check_dependencies():
        print("📦 Missing dependencies, installing...")
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            print("   Please run: pip install -r requirements.txt")
            return False
        print("✅ Dependencies installed successfully")
    
    # Run the main app
    print("\n🔄 Starting LQQ3 Signal App...")
    try:
        result = subprocess.run([sys.executable, "lqq3_signal_app.py"], 
                               capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running app: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Signal check completed successfully")
    else:
        print("❌ Signal check failed")
    
    # Keep window open on Windows
    if os.name == 'nt':
        input("\nPress Enter to exit...")
    
    sys.exit(0 if success else 1)
