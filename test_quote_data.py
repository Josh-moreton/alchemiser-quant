#!/usr/bin/env python3
"""
Test script to diagnose FTLS and LEU quote data issues using AWS Secrets Manager
"""
import logging

from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

logging.basicConfig(level=logging.DEBUG)


def main():
    try:
        print("Initializing SecretsManager...")
        sm = SecretsManager()

        print("Getting Alpaca credentials from AWS Secrets Manager...")
        api_key, secret_key = sm.get_alpaca_keys(paper_trading=True)

        if not api_key or not secret_key:
            print("ERROR: Failed to retrieve Alpaca credentials from AWS Secrets Manager")
            return

        print(f"Successfully retrieved credentials (API key starts with: {api_key[:8]}...)")

        print("Initializing AlpacaManager...")
        manager = AlpacaManager(str(api_key), str(secret_key), paper=True)

        # Test quote retrieval for problematic symbols plus some known working ones
        test_symbols = ["FTLS", "LEU", "AAPL", "TSLA", "BIL", "OKLO"]

        for symbol in test_symbols:
            print(f"\n=== Testing {symbol} ===")

            try:
                # Test raw quote from Alpaca API
                print(f"Getting raw quote for {symbol}...")
                raw_quote = manager.get_latest_quote_raw(symbol)

                if raw_quote:
                    print(f"✅ Raw quote found for {symbol}")
                    print(f"   Bid: {getattr(raw_quote, 'bid_price', 'N/A')}")
                    print(f"   Ask: {getattr(raw_quote, 'ask_price', 'N/A')}")
                    print(f"   Timestamp: {getattr(raw_quote, 'timestamp', 'N/A')}")

                    # Check if bid/ask are valid
                    bid = float(getattr(raw_quote, "bid_price", 0))
                    ask = float(getattr(raw_quote, "ask_price", 0))
                    print(f"   Bid > 0: {bid > 0}, Ask > 0: {ask > 0}, Bid < Ask: {bid < ask}")
                else:
                    print(f"❌ No raw quote data for {symbol}")

                # Test processed quote
                print(f"Getting processed quote for {symbol}...")
                quote = manager.get_latest_quote(symbol)

                if quote:
                    print(f"✅ Processed quote: {quote}")
                else:
                    print(f"❌ No processed quote for {symbol}")

            except Exception as e:
                print(f"❌ Error getting quote for {symbol}: {e}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
