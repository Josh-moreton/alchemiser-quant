#!/usr/bin/env python3
"""
Quick test of the LSE Portfolio Optimizer with a small subset of tickers
"""

import pandas as pd
import yfinance as yf

# Test with a small subset first
def test_small_subset():
    print("Testing LSE Portfolio Optimizer with small subset...")
    
    # Load the CSV
    df = pd.read_csv('All_LSE.csv')
    
    # Get a small subset of different asset types
    shares = df[df['MiFIR Identifier Code'] == 'SHRS']['Ticker'].head(5).tolist()
    etfs = df[df['MiFIR Identifier Code'] == 'ETFS']['Ticker'].head(5).tolist()
    etns = df[df['MiFIR Identifier Code'] == 'ETNS']['Ticker'].head(3).tolist()
    
    test_tickers = shares + etfs + etns
    print(f"Testing with {len(test_tickers)} tickers: {test_tickers}")
    
    # Test downloading a few with .L suffix
    valid_tickers = []
    for ticker in test_tickers:
        ticker_with_suffix = ticker + ".L"
        try:
            data = yf.download(ticker_with_suffix, period="1mo", progress=False)
            if not data.empty and 'Close' in data.columns:
                valid_tickers.append(ticker_with_suffix)
                print(f"✓ {ticker_with_suffix} - Valid data")
            else:
                print(f"✗ {ticker_with_suffix} - No data")
        except Exception as e:
            print(f"✗ {ticker_with_suffix} - Error: {str(e)[:50]}")
    
    print(f"\nFound {len(valid_tickers)} valid tickers out of {len(test_tickers)} tested")
    return valid_tickers

if __name__ == "__main__":
    test_small_subset()
