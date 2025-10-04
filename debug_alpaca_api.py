#!/usr/bin/env python3
"""Debug script to show exact Alpaca API call details."""

from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

# Add project root to path
_project_root = Path(__file__).resolve().parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys

# Get credentials
api_key, secret_key, endpoint = get_alpaca_keys()
print(f"🔑 Using endpoint: {endpoint}")
print(f"🔑 API Key: {api_key[:10]}...{api_key[-4:]}")
print()

# Initialize client
client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

# Calculate date range (same as backtest_download.py)
end_date = datetime.now(timezone.utc).replace(
    hour=0, minute=0, second=0, microsecond=0
) - timedelta(days=1)
start_date = end_date - timedelta(days=30)  # Just 30 days for testing

symbol = "SPY"

print(f"📅 Date Range:")
print(f"   Start: {start_date} ({start_date.isoformat()})")
print(f"   End:   {end_date} ({end_date.isoformat()})")
print(f"   End+1: {end_date + timedelta(days=1)} (Alpaca end is exclusive)")
print()

# Create request
request = StockBarsRequest(
    symbol_or_symbols=symbol,
    timeframe=TimeFrame.Day,
    start=start_date,
    end=end_date + timedelta(days=1),
    adjustment="all",
)

print(f"📊 Request Details:")
print(f"   Symbol: {request.symbol_or_symbols}")
print(f"   Timeframe: {request.timeframe}")
print(f"   Start: {request.start}")
print(f"   End: {request.end}")
print(f"   Adjustment: {request.adjustment}")
print()

# Make the API call
print(f"🌐 Making API call to Alpaca...")
try:
    bars_dict = client.get_stock_bars(request)

    print(f"✅ API call successful!")
    print(f"   Response type: {type(bars_dict)}")
    print(f"   String repr: {str(bars_dict)[:200]}")

    # Check various attributes
    attrs_to_check = ["data", "df", "dict", "__dict__", "bars"]
    for attr in attrs_to_check:
        if hasattr(bars_dict, attr):
            val = getattr(bars_dict, attr)
            print(f"   Has .{attr}: {type(val)}")
            if isinstance(val, dict):
                print(f"      Keys: {list(val.keys())[:5]}")
    print()

    # Try different ways to access the data
    bars = None

    # Try direct dict access (this is what the current code does)
    try:
        if symbol in bars_dict:
            print(f"   ✓ Direct dict access worked: {symbol} in bars_dict")
            bars = bars_dict[symbol]
        else:
            print(f"   ✗ Direct dict access failed: {symbol} not in bars_dict")
    except (KeyError, TypeError) as e:
        print(f"   ✗ Direct dict access error: {e}")

    # Try .data attribute
    if bars is None and hasattr(bars_dict, "data"):
        try:
            if isinstance(bars_dict.data, dict) and symbol in bars_dict.data:
                print(f"   ✓ .data dict access worked")
                bars = bars_dict.data[symbol]
        except Exception as e:
            print(f"   ✗ .data access error: {e}")

    if bars:
        print(f"📈 Data for {symbol}:")
        print(f"   Type: {type(bars)}")
        print(f"   Length: {len(bars) if hasattr(bars, '__len__') else 'N/A'}")

        if bars and len(bars) > 0:
            print(f"\n   First bar:")
            first_bar = bars[0]
            print(f"      Timestamp: {first_bar.timestamp}")
            print(f"      Open: {first_bar.open}")
            print(f"      High: {first_bar.high}")
            print(f"      Low: {first_bar.low}")
            print(f"      Close: {first_bar.close}")
            print(f"      Volume: {first_bar.volume}")

            print(f"\n   Last bar:")
            last_bar = bars[-1]
            print(f"      Timestamp: {last_bar.timestamp}")
            print(f"      Open: {last_bar.open}")
            print(f"      High: {last_bar.high}")
            print(f"      Low: {last_bar.low}")
            print(f"      Close: {last_bar.close}")
            print(f"      Volume: {last_bar.volume}")
        else:
            print(f"   ⚠️  No bars returned!")
    else:
        print(f"❌ No bars found for symbol '{symbol}'!")

except Exception as e:
    print(f"❌ API call failed!")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Error message: {str(e)}")
    import traceback

    print(f"\n   Full traceback:")
    traceback.print_exc()

print()
print("=" * 60)
print("For Postman/cURL:")
print(f"Endpoint: https://data.alpaca.markets/v2/stocks/bars")
print(f"Method: GET")
print(f"Headers:")
print(f"  APCA-API-KEY-ID: {api_key}")
print(f"  APCA-API-SECRET-KEY: {secret_key}")
print(f"Query Parameters:")
print(f"  symbols: {symbol}")
print(f"  timeframe: 1Day")
print(f"  start: {start_date.isoformat()}")
print(f"  end: {(end_date + timedelta(days=1)).isoformat()}")
print(f"  adjustment: all")
print("=" * 60)
