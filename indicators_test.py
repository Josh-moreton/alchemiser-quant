
import requests
import time
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
from core.secrets_manager import get_secret

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our own indicators and data provider
from core.indicators import TechnicalIndicators
from core.data_provider import UnifiedDataProvider

BASE_URL = "https://api.twelvedata.com"

def get_twelvedata_api_key():
    # Fetch TwelveData API key from AWS Secrets Manager
    return get_secret("nuclear-secrets").get("TWELVEDATA_KEY")

# Global rate limiting variables
REQUEST_COUNT = 0
LAST_RESET_TIME = datetime.now()
MAX_REQUESTS_PER_MINUTE = 7  # Conservative limit (API allows 8, we use 7 for safety)

# All symbols we use in our strategies
ALL_SYMBOLS = [
    # Nuclear strategy symbols
    'SPY', 'IOO', 'TQQQ', 'VTV', 'XLF', 'VOX',  # Market symbols
    'UVXY', 'BTAL',  # Volatility symbols
    'QQQ', 'SQQQ', 'PSQ', 'UPRO',  # Tech symbols
    'TLT', 'IEF',  # Bond symbols
    'SMR', 'BWXT', 'LEU', 'EXC', 'NLR', 'OKLO',  # Nuclear symbols
    
    # TECL strategy symbols  
    'XLK', 'KMLM', 'SPXL', 'TECL', 'BIL', 'BSV'  # Additional TECL symbols
]

# Remove duplicates and sort
SYMBOLS = sorted(list(set(ALL_SYMBOLS)))

# All indicator periods we actually use (from analyzing the code)
INDICATOR_CONFIGS = [
    ('rsi', [9, 10, 20]),  # RSI periods we use across both strategies
    ('sma', [20, 200]),    # Moving average periods we use across both strategies
]

# All additional indicators we calculate but can't compare with TwelveData
OUR_CUSTOM_INDICATORS = [
    ('ma_return', [90]),    # Moving average return - 90 day period
    ('cum_return', [60]),   # Cumulative return - 60 day period  
]

def rate_limit_check():
    """Check and enforce rate limiting before making API calls."""
    global REQUEST_COUNT, LAST_RESET_TIME
    
    current_time = datetime.now()
    
    # Reset counter if more than a minute has passed
    if current_time - LAST_RESET_TIME >= timedelta(minutes=1):
        REQUEST_COUNT = 0
        LAST_RESET_TIME = current_time
        print(f"  🔄 Rate limit counter reset at {current_time.strftime('%H:%M:%S')}")
    
    # If we're at the limit, wait until the next minute
    if REQUEST_COUNT >= MAX_REQUESTS_PER_MINUTE:
        seconds_to_wait = 60 - (current_time - LAST_RESET_TIME).seconds
        if seconds_to_wait > 0:
            print(f"  ⏳ Rate limit reached ({REQUEST_COUNT}/{MAX_REQUESTS_PER_MINUTE}). Waiting {seconds_to_wait} seconds...")
            time.sleep(seconds_to_wait + 1)  # Add 1 second buffer
            REQUEST_COUNT = 0
            LAST_RESET_TIME = datetime.now()

def get_twelvedata_indicator(symbol, indicator, period, api_key):
    """Get current (latest) value from TwelveData API with proper rate limiting."""
    global REQUEST_COUNT
    rate_limit_check()
    url = f"{BASE_URL}/{indicator}"
    params = {
        "symbol": symbol,
        "interval": "1day",
        "time_period": period,
        "apikey": api_key,
        "outputsize": 1
    }
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        REQUEST_COUNT += 1
        resp = requests.get(url, params=params)
        data = resp.json()
        if "status" in data and data["status"] == "error":
            if "API call frequency" in data.get("message", "") or "run out of API credits" in data.get("message", ""):
                print(f"  ⚠️ Rate limit hit for {symbol} {indicator}({period}) - attempt {retry_count + 1}")
                REQUEST_COUNT = MAX_REQUESTS_PER_MINUTE
                time.sleep(2)
                retry_count += 1
                continue
            else:
                print(f"  ❌ API Error for {symbol} {indicator}({period}): {data.get('message', 'Unknown error')}")
                return None
        if "values" not in data or not data["values"]:
            print(f"  ⚠️ No data for {symbol} {indicator}({period})")
            return None
        latest = data["values"][0]
        return float(latest[indicator])
    print(f"  ❌ Failed to get {symbol} {indicator}({period}) after {max_retries} attempts")
    return None

def get_our_indicators(symbol):
    """Get our locally calculated indicators using our own logic and Alpaca data."""
    try:
        # Use our data provider to get historical data
        data_provider = UnifiedDataProvider(paper_trading=True)
        df = data_provider.get_data(symbol, period="1y", interval="1d")
        
        if df.empty:
            print(f"  No data from Alpaca for {symbol}")
            return None
            
        close_prices = df['Close']
        indicators = TechnicalIndicators()
        
        # Calculate RSI for all periods we actually use
        rsi_9 = indicators.rsi(close_prices, 9)
        rsi_10 = indicators.rsi(close_prices, 10)
        rsi_20 = indicators.rsi(close_prices, 20)
        
        # Calculate moving averages for all periods we actually use
        ma_20 = indicators.moving_average(close_prices, 20)
        ma_200 = indicators.moving_average(close_prices, 200)
        
        # Calculate additional indicators
        ma_return_90 = indicators.moving_average_return(close_prices, 90)
        cum_return_60 = indicators.cumulative_return(close_prices, 60)
        
        # Validate our moving averages are different (debugging the issue you found)
        if abs(ma_20.iloc[-1] - ma_200.iloc[-1]) < 0.01:
            print(f"  ⚠️ WARNING: MA(20) and MA(200) are nearly identical for {symbol}!")
            print(f"    This suggests a data or calculation issue.")
        
        # Build our indicators dict with proper error handling
        our_indicators = {
            'current_price': float(close_prices.iloc[-1]),
            'rsi_9': float(rsi_9.iloc[-1]) if not rsi_9.isna().iloc[-1] else 50.0,
            'rsi_10': float(rsi_10.iloc[-1]) if not rsi_10.isna().iloc[-1] else 50.0,
            'rsi_20': float(rsi_20.iloc[-1]) if not rsi_20.isna().iloc[-1] else 50.0,
            'ma_20': float(ma_20.iloc[-1]) if not ma_20.isna().iloc[-1] else close_prices.iloc[-1],
            'ma_200': float(ma_200.iloc[-1]) if not ma_200.isna().iloc[-1] else close_prices.iloc[-1],
            'ma_return_90': float(ma_return_90.iloc[-1]) if not ma_return_90.isna().iloc[-1] else 0.0,
            'cum_return_60': float(cum_return_60.iloc[-1]) if not cum_return_60.isna().iloc[-1] else 0.0,
        }
        
        return our_indicators
        
    except Exception as e:
        print(f"  Error calculating our indicators for {symbol}: {e}")
        return None

def validate_single_symbol(symbol):
    """Validate all indicators for a single symbol."""
    print(f"\n🔍 VALIDATING {symbol}")
    print("=" * 60)
    
    # Get our indicators
    our_indicators = get_our_indicators(symbol)
    if not our_indicators:
        print(f"❌ Failed to get our indicators for {symbol}")
        return
    
    print(f"💰 Current Price: ${our_indicators['current_price']:.2f}")
    
    # Validate RSI values
    print("\n📈 RSI VALIDATION:")
    rsi_periods = [9, 10, 20]
    api_key = get_twelvedata_api_key()
    for period in rsi_periods:
        our_rsi = our_indicators[f'rsi_{period}']
        td_rsi = get_twelvedata_indicator(symbol, 'rsi', period, api_key)
        
        if td_rsi is not None:
            diff = abs(our_rsi - td_rsi)
            status = "✅" if diff < 1.0 else "⚠️" if diff < 2.0 else "❌"
            print(f"  RSI({period:2d}): Our={our_rsi:5.1f} | TwelveData={td_rsi:5.1f} | Diff={diff:4.1f} {status}")
        else:
            print(f"  RSI({period:2d}): Our={our_rsi:5.1f} | TwelveData=N/A")
    
    # Validate Moving Averages
    print("\n📊 MOVING AVERAGE VALIDATION:")
    ma_periods = [20, 200]
    for period in ma_periods:
        our_ma = our_indicators[f'ma_{period}']
        td_ma = get_twelvedata_indicator(symbol, 'sma', period, api_key)
        
        if td_ma is not None:
            diff = abs(our_ma - td_ma)
            pct_diff = (diff / td_ma) * 100
            status = "✅" if pct_diff < 0.1 else "⚠️" if pct_diff < 0.5 else "❌"
            print(f"  MA({period:3d}): Our={our_ma:7.2f} | TwelveData={td_ma:7.2f} | Diff={diff:5.2f} ({pct_diff:.2f}%) {status}")
        else:
            print(f"  MA({period:3d}): Our={our_ma:7.2f} | TwelveData=N/A")
    
    # Show our additional indicators (not available from TwelveData)
    print("\n🔢 OUR ADDITIONAL INDICATORS:")
    print(f"  MA Return (90d): {our_indicators['ma_return_90']:6.2f}%")
    print(f"  Cum Return(60d): {our_indicators['cum_return_60']:6.2f}%")

def validate_trades(symbols=None, output_report=True):
    """
    Validate indicators for a list of symbols (or all by default) after live trades.
    Returns a summary dict and optionally writes a Markdown report.
    """
    global REQUEST_COUNT, LAST_RESET_TIME
    REQUEST_COUNT = 0
    LAST_RESET_TIME = datetime.now()
    failed_symbols = []
    report_rows = []
    if symbols is None:
        test_symbols = SYMBOLS
    else:
        test_symbols = symbols
    print(f"\n🚀 Running post-trade validation on {len(test_symbols)} symbols...")
    for i, symbol in enumerate(test_symbols, 1):
        print(f"\n[{i:2d}/{len(test_symbols)}] ", end="")
        try:
            from io import StringIO
            import contextlib
            buf = StringIO()
            with contextlib.redirect_stdout(buf):
                validate_single_symbol(symbol)
            output = buf.getvalue()
            report_rows.append((symbol, output))
        except Exception as e:
            print(f"❌ FAILED to validate {symbol}: {e}")
            failed_symbols.append(symbol)
            report_rows.append((symbol, f"❌ FAILED to validate {symbol}: {e}"))
        print(f"\n📊 Rate Limit Status: {REQUEST_COUNT}/{MAX_REQUESTS_PER_MINUTE} requests used this minute")
        if i < len(test_symbols):
            print(f"⏳ Moving to next symbol...")
            time.sleep(1)
    successful = len(test_symbols) - len(failed_symbols)
    summary = {
        "total": len(test_symbols),
        "successful": successful,
        "failed": failed_symbols,
        "report_path": None
    }
    if output_report:
        report_path = "indicator_validation_report.md"
        with open(report_path, "w") as f:
            f.write(f"# Technical Indicator Validation Report\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Symbols tested:** {len(test_symbols)}\n\n")
            f.write(f"**Rate limit:** {MAX_REQUESTS_PER_MINUTE} requests/minute\n\n")
            f.write(f"**Summary:**\n\n")
            f.write(f"- ✅ Successfully validated: {successful}/{len(test_symbols)} symbols\n")
            if failed_symbols:
                f.write(f"- ❌ Failed symbols: {', '.join(failed_symbols)}\n")
            else:
                f.write(f"- 🎉 All test symbols validated successfully!\n")
            f.write(f"\n---\n\n")
            for symbol, output in report_rows:
                f.write(f"## {symbol}\n\n")
                f.write(f"```")
                f.write(output)
                f.write(f"```\n\n")
        print(f"\n📄 Markdown report written to: {report_path}")
        summary["report_path"] = report_path
    return summary

# Remove CLI main()

if __name__ == "__main__":
    main()