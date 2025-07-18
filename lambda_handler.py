import sys
from main import run_live_trading_bot

def lambda_handler(event=None, context=None):
    result = run_live_trading_bot()
    return {"status": "success" if result else "failed"}
