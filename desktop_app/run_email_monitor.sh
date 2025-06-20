#!/bin/bash

# LQQ3 Email Monitor - Automator Script
# This script runs the email monitor and shows notifications

# Set the working directory
cd "$(dirname "$0")" || exit 1

# Check if it's a weekday (Monday=1, Sunday=7)
day_of_week=$(date +%u)
if [ "$day_of_week" -gt 5 ]; then
    echo "Weekend - skipping signal check"
    exit 0
fi

# Check if market is likely open (rough time check)
hour=$(date +%H)
if [ "$hour" -lt 6 ] || [ "$hour" -gt 16 ]; then
    echo "Outside market hours - skipping signal check"
    exit 0
fi

echo "Running LQQ3 Signal Monitor..."

# Run the email monitor
python3 lqq3_email_monitor.py

# Check if the command succeeded
if [ $? -eq 0 ]; then
    # Success notification
    osascript -e 'display notification "LQQ3 signal check completed successfully" with title "LQQ3 Monitor" sound name "Glass"'
    echo "✅ Signal check completed successfully"
else
    # Error notification
    osascript -e 'display notification "LQQ3 signal check failed - check your setup" with title "LQQ3 Monitor" sound name "Basso"'
    echo "❌ Signal check failed"
    exit 1
fi
