"""Quick script to check EDZ fractionability."""

import os

from alpaca.trading.client import TradingClient

# Get credentials from environment
api_key = os.environ.get("ALPACA_API_KEY")
api_secret = os.environ.get("ALPACA_API_SECRET")

if not api_key or not api_secret:
    print("ERROR: ALPACA_API_KEY and ALPACA_API_SECRET must be set")
    exit(1)

# Create client
client = TradingClient(api_key, api_secret, paper=False)

# Get EDZ asset info
asset = client.get_asset("EDZ")
print("EDZ Asset Info:")
print(f"  Symbol: {asset.symbol}")
print(f"  Tradable: {asset.tradable}")
print(f"  Fractionable: {asset.fractionable}")
print(f"  Class: {asset.asset_class}")
print(f"  Exchange: {asset.exchange}")

# Get current position
try:
    position = client.get_open_position("EDZ")
    print("\nCurrent EDZ Position:")
    print(f"  Quantity: {position.qty}")
    print(f"  Market Value: ${position.market_value}")
    print(f"  Current Price: ${position.current_price}")
except Exception as e:
    print(f"\nNo position or error: {e}")
