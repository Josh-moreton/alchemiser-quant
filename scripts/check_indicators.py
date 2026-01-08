"""Check indicator values for TECL.

Business Unit: debugging | Status: development.
"""
import sys
sys.path.insert(0, "layers/shared")
sys.path.insert(0, "functions/strategy_worker")
import os
os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"

from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
import pandas as pd

adapter = CachedMarketDataAdapter()

# Get TECL data
bars = adapter.get_bars("TECL", "1Y", "1Day")
df = pd.DataFrame([{"date": b.timestamp, "close": b.close} for b in bars])
df.set_index("date", inplace=True)
print(f"TECL data shape: {df.shape}")
print(f"Latest date: {df.index[-1]}")
print(f"Latest close: {df['close'].iloc[-1]}")

# Calculate 10-day moving average return
returns = df['close'].pct_change()
ma_return = returns.rolling(10).mean().iloc[-1] * 100  # Convert to percentage
print(f"TECL 10d MA Return: {ma_return:.4f}%")

# Calculate 10-day RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(10).mean()
loss = (-delta.where(delta < 0, 0)).rolling(10).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
print(f"TECL 10d RSI: {rsi.iloc[-1]:.4f}")

# Calculate 10-day stdev of returns
stdev_return = returns.rolling(10).std().iloc[-1] * 100
print(f"TECL 10d StdDev Return: {stdev_return:.4f}%")

# Now check SOXL
print("\n" + "="*50)
bars2 = adapter.get_bars("SOXL", "1Y", "1Day")
df2 = pd.DataFrame([{"date": b.timestamp, "close": b.close} for b in bars2])
df2.set_index("date", inplace=True)
print(f"SOXL data shape: {df2.shape}")
print(f"Latest date: {df2.index[-1]}")
print(f"Latest close: {df2['close'].iloc[-1]}")

returns2 = df2['close'].pct_change()
ma_return2 = returns2.rolling(10).mean().iloc[-1] * 100
print(f"SOXL 10d MA Return: {ma_return2:.4f}%")

delta2 = df2['close'].diff()
gain2 = (delta2.where(delta2 > 0, 0)).rolling(10).mean()
loss2 = (-delta2.where(delta2 < 0, 0)).rolling(10).mean()
rs2 = gain2 / loss2
rsi2 = 100 - (100 / (1 + rs2))
print(f"SOXL 10d RSI: {rsi2.iloc[-1]:.4f}")

stdev_return2 = returns2.rolling(10).std().iloc[-1] * 100
print(f"SOXL 10d StdDev Return: {stdev_return2:.4f}%")
