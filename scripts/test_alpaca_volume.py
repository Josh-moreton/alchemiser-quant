#!/usr/bin/env python3
"""Quick test script to verify we can get current price AND volume from Alpaca."""

import os
import sys

from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


def test_latest_trade_volume():
    """Test fetching latest trade which includes volume."""
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestTradeRequest, StockLatestQuoteRequest

    api_key = os.environ.get("ALPACA__KEY") or os.environ.get("ALPACA_KEY")
    secret_key = os.environ.get("ALPACA__SECRET") or os.environ.get("ALPACA_SECRET")

    if not api_key or not secret_key:
        print("❌ No Alpaca credentials found in environment")
        return

    client = StockHistoricalDataClient(api_key, secret_key)

    symbols = ["SPY", "AAPL", "MSFT"]

    print("\n=== Testing Latest Quote (bid/ask/mid price) ===")
    try:
        quote_request = StockLatestQuoteRequest(symbol_or_symbols=symbols)
        quotes = client.get_stock_latest_quote(quote_request)

        for symbol in symbols:
            quote = quotes.get(symbol)
            if quote:
                bid = float(quote.bid_price)
                ask = float(quote.ask_price)
                mid = (bid + ask) / 2
                print(f"  {symbol}: bid=${bid:.2f}, ask=${ask:.2f}, mid=${mid:.2f}")
            else:
                print(f"  {symbol}: No quote data")
    except Exception as e:
        print(f"❌ Quote error: {e}")

    print("\n=== Testing Latest Trade (price + volume) ===")
    try:
        trade_request = StockLatestTradeRequest(symbol_or_symbols=symbols)
        trades = client.get_stock_latest_trade(trade_request)

        for symbol in symbols:
            trade = trades.get(symbol)
            if trade:
                price = float(trade.price)
                size = int(trade.size)  # This is the trade size (volume of that trade)
                timestamp = trade.timestamp
                print(f"  {symbol}: price=${price:.2f}, trade_size={size}, time={timestamp}")
            else:
                print(f"  {symbol}: No trade data")
    except Exception as e:
        print(f"❌ Trade error: {e}")

    print("\n=== Testing Today's Bars (includes cumulative volume) ===")
    try:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from datetime import datetime, timedelta

        # Get today's date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        bars_request = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Day,
            start=yesterday,
            end=today,
        )
        bars = client.get_stock_bars(bars_request)

        for symbol in symbols:
            symbol_bars = bars.get(symbol, [])
            if symbol_bars:
                for bar in symbol_bars:
                    print(
                        f"  {symbol}: date={bar.timestamp.date()}, "
                        f"O=${float(bar.open):.2f}, H=${float(bar.high):.2f}, "
                        f"L=${float(bar.low):.2f}, C=${float(bar.close):.2f}, "
                        f"volume={int(bar.volume):,}"
                    )
            else:
                print(f"  {symbol}: No bar data for today/yesterday")
    except Exception as e:
        print(f"❌ Bars error: {e}")

    print("\n=== Testing Snapshot (combines quote + trade + bar) ===")
    try:
        from alpaca.data.requests import StockSnapshotRequest

        snapshot_request = StockSnapshotRequest(symbol_or_symbols=symbols)
        snapshots = client.get_stock_snapshot(snapshot_request)

        for symbol in symbols:
            snap = snapshots.get(symbol)
            if snap:
                # Latest quote
                if snap.latest_quote:
                    bid = float(snap.latest_quote.bid_price)
                    ask = float(snap.latest_quote.ask_price)
                    print(f"  {symbol} quote: bid=${bid:.2f}, ask=${ask:.2f}")

                # Latest trade
                if snap.latest_trade:
                    price = float(snap.latest_trade.price)
                    size = int(snap.latest_trade.size)
                    print(f"  {symbol} trade: price=${price:.2f}, size={size}")

                # Daily bar (includes volume)
                if snap.daily_bar:
                    vol = int(snap.daily_bar.volume)
                    close = float(snap.daily_bar.close)
                    print(f"  {symbol} daily_bar: close=${close:.2f}, volume={vol:,}")

                # Previous daily bar
                if snap.previous_daily_bar:
                    prev_close = float(snap.previous_daily_bar.close)
                    prev_vol = int(snap.previous_daily_bar.volume)
                    print(
                        f"  {symbol} prev_bar: close=${prev_close:.2f}, volume={prev_vol:,}"
                    )
            else:
                print(f"  {symbol}: No snapshot data")
    except Exception as e:
        print(f"❌ Snapshot error: {e}")

    print("\n✅ Test complete!")
    print("\nRECOMMENDATION:")
    print("  Use StockSnapshotRequest - it gives us:")
    print("  - latest_quote.bid_price/ask_price → mid price for 'close'")
    print("  - daily_bar.volume → today's cumulative volume")
    print("  - daily_bar.open/high/low → today's OHLC for synthetic bar")


if __name__ == "__main__":
    test_latest_trade_volume()
