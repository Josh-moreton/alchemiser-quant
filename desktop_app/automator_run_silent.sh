#!/bin/bash

# LQQ3 Email Monitor - Silent Automator Script (no popups)
# This script runs silently and only logs to a file

# Change to the project directory
cd /Users/joshmoreton/GitHub/LQQ3/desktop_app

# Activate the virtual environment
source ../.venv/bin/activate

# Create a log file with timestamp
LOG_FILE="lqq3_monitor.log"
echo "$(date): Running LQQ3 signal check..." >> "$LOG_FILE"

# Run the email monitor and capture output
python lqq3_email_monitor.py >> "$LOG_FILE" 2>&1

# Check if the command succeeded
if [ $? -eq 0 ]; then
    echo "$(date): ✅ Signal check completed successfully" >> "$LOG_FILE"
    # Try notification (silent if permissions not granted)
    osascript -e 'display notification "LQQ3 signal check completed" with title "LQQ3 Monitor"' 2>/dev/null
else
    echo "$(date): ❌ Signal check failed" >> "$LOG_FILE"
    exit 1
fi
