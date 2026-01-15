#!/usr/bin/env python3
"""Quick test of Alpaca data fetching."""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment

load_dotenv()

api_key = os.environ.get("ALPACA__KEY")
api_secret = os.environ.get("ALPACA__SECRET")
print(f"API Key found: {bool(api_key)}")
print(f"API Secret found: {bool(api_secret)}")

client = StockHistoricalDataClient(api_key, api_secret)
print("Client created")

# Try fetching SPY
end_dt = datetime.now() - timedelta(days=1)
start_dt = end_dt - timedelta(days=10)
print(f"Fetching SPY from {start_dt} to {end_dt}")

try:
    request = StockBarsRequest(
        symbol_or_symbols="SPY",
        timeframe=TimeFrame.Day,
        start=start_dt,
        end=end_dt,
        adjustment=Adjustment.ALL,
    )
    response = client.get_stock_bars(request)
    print(f"Response type: {type(response)}")
    print(f"Response data attribute: {hasattr(response, 'data')}")
    
    # Try different access methods
    try:
        bars = response["SPY"]
        print(f"Direct access works, bars count: {len(bars) if bars else 0}")
        if bars:
            print(f"Last bar date: {bars[-1].timestamp}")
            print(f"Last bar close: {bars[-1].close}")
    except Exception as e1:
        print(f"Direct access failed: {e1}")
        
    # Try .data attribute
    if hasattr(response, 'data'):
        print(f"Data attribute type: {type(response.data)}")
        if "SPY" in response.data:
            bars = response.data["SPY"]
            print(f"Data access works, bars count: {len(bars) if bars else 0}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
