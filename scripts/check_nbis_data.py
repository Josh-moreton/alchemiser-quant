#!/usr/bin/env python3
"""Check NBIS data from Alpaca API."""
from dotenv import load_dotenv
load_dotenv()

import os
from datetime import datetime, timezone
from alpaca.data.enums import Adjustment
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pytz

api_key = os.environ.get('ALPACA_KEY')
api_secret = os.environ.get('ALPACA_SECRET')
client = StockHistoricalDataClient(api_key, api_secret)

print("=" * 60)
print("NBIS Daily Bars from Alpaca")
print("=" * 60)

# Get daily bars for NBIS around Jan 15
request = StockBarsRequest(
    symbol_or_symbols='NBIS',
    timeframe=TimeFrame(1, TimeFrameUnit.Day),
    start=datetime(2026, 1, 10, tzinfo=timezone.utc),
    end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=timezone.utc),
    adjustment=Adjustment.ALL,
)

response = client.get_stock_bars(request)
bars = list(response.data.get('NBIS', []))
for bar in bars:
    print(f"  {bar.timestamp.date()} Close: {bar.close}")

print()
print("=" * 60)
print("NBIS 15-minute bars on Jan 15 (3:30-4:00 PM ET)")
print("=" * 60)

et_tz = pytz.timezone("America/New_York")
bar_start_et = et_tz.localize(datetime(2026, 1, 15, 15, 30, 0))
bar_end_et = et_tz.localize(datetime(2026, 1, 15, 16, 0, 0))

request2 = StockBarsRequest(
    symbol_or_symbols='NBIS',
    timeframe=TimeFrame(15, TimeFrameUnit.Minute),
    start=bar_start_et.astimezone(pytz.UTC),
    end=bar_end_et.astimezone(pytz.UTC),
    adjustment=Adjustment.ALL,
)

response2 = client.get_stock_bars(request2)
bars2 = list(response2.data.get('NBIS', []))
for bar in bars2:
    bar_et = bar.timestamp.astimezone(et_tz)
    print(f"  {bar_et.strftime('%H:%M ET')} Close: {bar.close}")

print()
print("The 3:45 PM close (bar starting at 3:30) should be used as simulated live bar")
