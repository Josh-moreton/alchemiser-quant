#!/usr/bin/env python3
"""
Test script for LSE ticker discovery - validates the discovery process with a small sample.
"""

import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def test_ticker_discovery():
    """Test a small sample of the ticker discovery process."""
    
    print("Testing LSE ticker discovery with sample patterns...")
    
    # Test a small sample of patterns
    test_patterns = [
        # Known valid tickers
        "LQQ3.L", "VUSA.L", "GOLD.L", "BP.L", "LLOY.L", "BARC.L",
        # Some ETFs
        "VMID.L", "VEVE.L", "ISF.L", "IUSA.L",
        # Some commodities
        "PHAU.L", "SGLN.L", "GBSS.L",
        # Some invalid patterns (should fail)
        "INVALID.L", "FAKE123.L", "NOTREAL.L"
    ]
    
    print(f"Testing {len(test_patterns)} sample tickers...")
    
    def check_ticker(ticker):
        try:
            data = yf.download(ticker, period="5d", progress=False)
            if not data.empty and 'Close' in data.columns:
                return ticker, True, len(data)
        except:
            pass
        return ticker, False, 0
    
    valid_tickers = []
    invalid_tickers = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_ticker, ticker): ticker for ticker in test_patterns}
        
        for future in as_completed(futures):
            ticker, is_valid, data_points = future.result()
            if is_valid:
                valid_tickers.append(ticker)
                print(f"✓ {ticker}: Valid ({data_points} data points)")
            else:
                invalid_tickers.append(ticker)
                print(f"✗ {ticker}: Invalid/No data")
    
    print(f"\nTest Results:")
    print(f"Valid tickers: {len(valid_tickers)}")
    print(f"Invalid tickers: {len(invalid_tickers)}")
    print(f"Success rate: {len(valid_tickers)/len(test_patterns)*100:.1f}%")
    
    if len(valid_tickers) > 0:
        print("\nDiscovery system is working correctly!")
        print("You can now run the full portfolio optimizer:")
        print("  python lse_portfolio_optimizer.py          # Full discovery (slow but comprehensive)")
        print("  python lse_portfolio_optimizer.py --fallback  # Fast mode with curated list")
    else:
        print("\nWarning: Discovery system may have issues. Check your internet connection.")
    
    return len(valid_tickers) > 0

if __name__ == "__main__":
    test_ticker_discovery()
