#!/usr/bin/env python3
"""
Enhanced LSE ticker discovery and validation test.
Tests multiple ticker formats and validation methods.
"""

import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

def advanced_ticker_validation(ticker):
    """Enhanced ticker validation with multiple checks."""
    try:
        # Method 1: Try ticker info first (fastest)
        ticker_obj = yf.Ticker(ticker)
        
        # Method 2: Try to get historical data
        data = yf.download(ticker, period="10d", progress=False, auto_adjust=True)
        
        if data.empty:
            return False, "No data available"
        
        # Handle multi-level columns
        if data.columns.nlevels > 1:
            data.columns = data.columns.get_level_values(0)
        
        if 'Close' not in data.columns:
            return False, "No Close price column"
        
        # Check for actual price data
        close_prices = data['Close'].dropna()
        if len(close_prices) == 0:
            return False, "No valid close prices"
        
        # Additional validation: reasonable price range
        if close_prices.min() <= 0:
            return False, "Invalid price data (zero/negative)"
        
        # Check for sufficient data variety (not all same price)
        if close_prices.std() == 0 and len(close_prices) > 1:
            return False, "Suspicious data (no price variation)"
        
        return True, f"Valid ({len(data)} days, price range: {close_prices.min():.2f}-{close_prices.max():.2f})"
        
    except Exception as e:
        return False, f"Error: {str(e)[:50]}"

def test_known_lse_tickers():
    """Test well-known LSE tickers with different formats."""
    
    print("Testing well-known LSE tickers with multiple formats...")
    print("=" * 60)
    
    # Test the same tickers with different suffix formats
    base_tickers = ["LQQ3", "VUSA", "BP", "LLOY", "BARC", "SHEL", "AZN"]
    suffixes = [".L", ".LN", ".LON", ".LSE"]
    
    test_tickers = []
    for base in base_tickers:
        for suffix in suffixes:
            test_tickers.append(f"{base}{suffix}")
    
    print(f"Testing {len(test_tickers)} ticker format combinations...")
    
    def test_single_ticker(ticker):
        return ticker, *advanced_ticker_validation(ticker)
    
    valid_results = []
    invalid_results = []
    
    # Test in parallel
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(test_single_ticker, ticker): ticker for ticker in test_tickers}
        
        for future in as_completed(futures):
            ticker, is_valid, message = future.result()
            
            if is_valid:
                valid_results.append((ticker, message))
                print(f"✓ {ticker:12} {message}")
            else:
                invalid_results.append((ticker, message))
                print(f"✗ {ticker:12} {message}")
    
    print(f"\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Valid tickers: {len(valid_results)}")
    print(f"Invalid tickers: {len(invalid_results)}")
    print(f"Success rate: {len(valid_results)/len(test_tickers)*100:.1f}%")
    
    if valid_results:
        print(f"\nWorking LSE ticker formats found:")
        for ticker, message in valid_results:
            print(f"  {ticker}")
        
        # Determine the best suffix format
        suffix_counts = {}
        for ticker, _ in valid_results:
            for suffix in suffixes:
                if ticker.endswith(suffix):
                    suffix_counts[suffix] = suffix_counts.get(suffix, 0) + 1
                    break
        
        if suffix_counts:
            best_suffix = max(suffix_counts, key=suffix_counts.get)
            print(f"\nBest LSE suffix format appears to be: {best_suffix}")
            print(f"Success rate by suffix:")
            for suffix, count in suffix_counts.items():
                total_tested = sum(1 for t in test_tickers if t.endswith(suffix))
                print(f"  {suffix:6} {count}/{total_tested} = {count/total_tested*100:.1f}%")
    
    return len(valid_results) > 0

def test_etf_discovery():
    """Test discovery of various ETF types."""
    
    print(f"\n" + "=" * 60)
    print("Testing ETF Discovery")
    print("=" * 60)
    
    # Known ETF patterns that should exist on LSE
    etf_patterns = [
        # Vanguard ETFs
        "VUSA.L", "VEUR.L", "VFEM.L", "VJPN.L", "VWRL.L", "VHYL.L",
        # iShares ETFs  
        "ISF.L", "IUSA.L", "IUKD.L", "IDEM.L", "IWDP.L", "IGOV.L",
        # Leveraged ETFs
        "3USL.L", "3USS.L", "QQQ3.L", "TQQQ.L", "EQQQ.L",
        # Commodity ETFs
        "PHAU.L", "SGLN.L", "GBSS.L", "PHYS.L", "PSLV.L",
        # Bond ETFs
        "GOVT.L", "GILT.L", "GILD.L", "TIPS.L"
    ]
    
    print(f"Testing {len(etf_patterns)} ETF patterns...")
    
    valid_etfs = []
    
    def test_etf(ticker):
        return ticker, *advanced_ticker_validation(ticker)
    
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(test_etf, ticker): ticker for ticker in etf_patterns}
        
        for future in as_completed(futures):
            ticker, is_valid, message = future.result()
            
            if is_valid:
                valid_etfs.append(ticker)
                print(f"✓ {ticker:12} {message}")
            else:
                print(f"✗ {ticker:12} {message}")
    
    print(f"\nETF Discovery Results:")
    print(f"Valid ETFs found: {len(valid_etfs)}")
    print(f"ETF success rate: {len(valid_etfs)/len(etf_patterns)*100:.1f}%")
    
    return valid_etfs

def main():
    print("Enhanced LSE Ticker Discovery Test")
    print("=" * 60)
    
    # Test 1: Known LSE tickers with different formats
    basic_success = test_known_lse_tickers()
    
    # Test 2: ETF discovery
    valid_etfs = test_etf_discovery()
    
    # Final recommendations
    print(f"\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    
    if basic_success:
        print("✓ Basic LSE ticker validation is working")
        print("✓ You can proceed with the portfolio optimizer")
        print("\nTo run the full analysis:")
        print("  python lse_portfolio_optimizer.py --fallback    # Use curated list (recommended)")
        print("  python lse_portfolio_optimizer.py              # Full discovery (experimental)")
    else:
        print("✗ LSE ticker validation has issues")
        print("✗ Check your internet connection or yfinance API status")
        print("✗ Consider using a different data source")
    
    if len(valid_etfs) > 10:
        print(f"✓ Good ETF coverage ({len(valid_etfs)} ETFs found)")
    else:
        print(f"⚠ Limited ETF coverage ({len(valid_etfs)} ETFs found)")
    
    return basic_success

if __name__ == "__main__":
    main()
