#!/usr/bin/env python3
"""
Nuclear Trading Dashboard - Quick Launcher
Starts the web dashboard for monitoring
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(script_dir, 'main.py')
    
    # Run the main script in dashboard mode
    result = subprocess.run([sys.executable, main_script, 'dashboard'], cwd=script_dir)
    sys.exit(result.returncode)
