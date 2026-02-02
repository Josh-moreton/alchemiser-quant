#!/bin/bash
# Daily P&L Excel export script for launchd/cron
# Runs after market close to update the local Excel dashboard

set -e

# Change to project directory
cd /Users/joshmoreton/GitHub/alchemiser-quant

# Activate virtual environment and run export
source venv/bin/activate
python scripts/pnl_report.py --excel

echo "$(date): P&L Excel export completed" >> /tmp/pnl_excel_cron.log
