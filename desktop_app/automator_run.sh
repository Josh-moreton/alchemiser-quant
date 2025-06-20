#!/bin/bash

# LQQ3 Email Monitor - Automator Script
# This script properly activates the virtual environment and runs the email monitor

# Change to the project directory
cd /Users/joshmoreton/GitHub/LQQ3/desktop_app

# Activate the virtual environment
source ../.venv/bin/activate

# Install requirements if needed (safety check)
pip install -q -r requirements.txt

# Run the email monitor
python lqq3_email_monitor.py

# Check if the command succeeded and show notification
if [ $? -eq 0 ]; then
    echo "✅ Signal check completed successfully"
    # Show a dialog box that's more reliable than notifications
    osascript -e 'display dialog "LQQ3 signal check completed successfully!" with title "LQQ3 Monitor" buttons {"OK"} default button "OK" with icon note giving up after 5'
    # Also try notification (might be blocked)
    osascript -e 'display notification "LQQ3 signal check completed successfully" with title "LQQ3 Monitor"'
else
    echo "❌ Signal check failed"
    osascript -e 'display dialog "LQQ3 signal check failed - check your setup" with title "LQQ3 Monitor" buttons {"OK"} default button "OK" with icon stop'
    exit 1
fi
