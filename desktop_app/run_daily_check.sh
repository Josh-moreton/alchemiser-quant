#!/bin/bash
# LQQ3 Daily Signal Check - macOS/Linux Launcher
# Double-click this file to run your daily signal check

cd "$(dirname "$0")"
python3 launch.py
read -p "Press Enter to exit..."
