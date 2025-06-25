#!/bin/bash

# LQQ3 Daily Signal Runner
# Runs the daily signal check at 8am with proper environment

# Change to the script directory
cd /Users/joshua.moreton/Documents/GitHub/LQQ3

# Activate virtual environment and run the script
source .venv/bin/activate
python lqq3_daily_signal.py

# Log the execution
echo "$(date): LQQ3 daily signal check completed" >> /Users/joshua.moreton/Documents/GitHub/LQQ3/daily_signal.log
