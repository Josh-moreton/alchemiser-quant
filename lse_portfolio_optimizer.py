#!/usr/bin/env python3
"""
London Stock Exchange Portfolio Optimizer
Tests ALL LSE tickers to find optimal 2-3 stock portfolios with LQQ3 as core holding.
Optimizes for Calmar ratio (CAGR / Max Drawdown).

This script discovers ALL tradeable instruments on the LSE including:
- Stocks (FTSE 100, FTSE 250, AIM, etc.)
- ETFs (equity, bond, commodity, currency, sector)
- Investment trusts
- REITs
- Bonds and fixed income instruments
- Commodities (gold, silver, oil, etc.)
- Currency hedged instruments
- Leveraged and inverse products

Usage:
    python lse_portfolio_optimizer.py           # Full discovery mode (comprehensive, 10-15 min)
    python lse_portfolio_optimizer.py --fallback   # Fast mode with curated list (5-10 min)
    
    First run: Use full discovery to find all available tickers
    Subsequent runs: Will reuse discovered tickers automatically
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time
import sys
import glob
import warnings
warnings.filterwarnings('ignore')

# --- Configuration ---
CORE_TICKER = "LQQ3.L"
CORE_WEIGHT = 0.66  # 66% allocation to LQQ3
START_DATE = "2011-01-01"  # Start date for analysis
END_DATE = None  # Use current date
INITIAL_CAPITAL = 65000
MIN_TRADING_DAYS = 252 * 2  # Minimum 2 years of data
REBALANCE_FREQUENCY = 'Q'  # Quarterly rebalancing ('D', 'W', 'M', 'Q')

# --- LSE Ticker Discovery ---
def get_all_lse_tickers():
    """
    Fetch all available LSE tickers from multiple sources.
    This includes stocks, ETFs, bonds, commodities, and all other tradeable instruments.
    """
    print("Discovering all LSE tickers...")
    all_tickers = set()
    
    # Method 1: Generate common LSE ticker patterns
    print("- Generating common LSE ticker patterns...")
    # Most LSE tickers end with .L
    # Generate patterns for 2-5 character codes
    base_patterns = []
    
    # Common 2-4 letter combinations
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    numbers = '0123456789'
    
    # 2-letter combinations (like BP, BT, etc.)
    for i in letters:
        for j in letters:
            base_patterns.append(f"{i}{j}")
    
    # 3-letter combinations (like AZN, GSK, etc.)
    for i in letters:
        for j in letters:
            for k in letters:
                base_patterns.append(f"{i}{j}{k}")
    
    # 4-letter combinations (like LLOY, BARC, etc.)
    for i in letters:
        for j in letters:
            for k in letters:
                for l in letters:
                    base_patterns.append(f"{i}{j}{k}{l}")
    
    # Add patterns with numbers (like 3IN, BT-A, etc.)
    for i in letters:
        for j in numbers:
            base_patterns.append(f"{i}{j}")
            base_patterns.append(f"{j}{i}")
    
    # Add specific common patterns
    specific_patterns = [
        # ETF patterns
        "VUSA", "VMID", "VEVE", "VFEM", "VJPN", "VEUR", "VGOV", "VWRL", "VHYL",
        "ISF", "IUSA", "IUKD", "IDEM", "IEVL", "IGOV", "IBTM", "IWDP", "IWMO",
        "TQQQ", "SQQQ", "QQQ3", "EQQQ", "3USL", "3USS", "LQQ3", "QQQL", "QQQS",
        # Bond ETFs
        "GOVT", "GILT", "GILD", "TIPS", "GLTA", "GLTB", "GLTL", "GLTS",
        # Commodity ETFs
        "GOLD", "PHAU", "SGLN", "GBSS", "SILV", "PSLV", "PHYS", "COIL", "CRUD",
        # Inverse/Leveraged ETFs
        "3OIL", "3GBP", "3USD", "BEAR", "BULL", "LBUY", "LSELL",
        # Currency ETFs
        "GBPU", "EURU", "JPYU", "CHFU", "CADU", "AUDU",
        # Sector ETFs
        "TECH", "FINU", "HCAR", "REAL", "CONS", "ENER", "HEAL", "INDA", "UTIL"
    ]
    
    base_patterns.extend(specific_patterns)
    
    # Convert to LSE format
    lse_tickers = [f"{pattern}.L" for pattern in base_patterns]
    all_tickers.update(lse_tickers)
    
    # Method 2: Try common international ticker patterns that might trade on LSE
    print("- Adding international patterns...")
    international_patterns = []
    
    # Add US ETF equivalents that might be available on LSE
    us_etfs = ["SPY", "QQQ", "IWM", "VTI", "VEA", "VWO", "BND", "TLT", "GLD", "SLV"]
    for etf in us_etfs:
        international_patterns.extend([f"{etf}.L", f"{etf}L.L", f"I{etf}.L", f"V{etf}.L"])
    
    all_tickers.update(international_patterns)
    
    # Method 3: Known LSE suffixes and exchanges
    print("- Adding various LSE exchange suffixes...")
    exchange_suffixes = [".L", ".LN", ".LSE"]
    base_tickers_no_suffix = [ticker.replace(".L", "") for ticker in list(all_tickers)]
    
    for suffix in exchange_suffixes:
        for base in base_tickers_no_suffix[:1000]:  # Limit to avoid too many
            all_tickers.add(f"{base}{suffix}")
    
    print(f"Generated {len(all_tickers)} potential ticker patterns")
    return list(all_tickers)

def validate_tickers_batch(tickers_batch, max_workers=20):
    """
    Validate a batch of tickers by attempting to download minimal data.
    Returns list of valid tickers.
    """
    valid_tickers = []
    
    def check_ticker(ticker):
        try:
            # Try to get just 5 days of data to check if ticker exists
            data = yf.download(ticker, period="5d", progress=False)
            if not data.empty and 'Close' in data.columns:
                return ticker
        except:
            pass
        return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_ticker, ticker): ticker for ticker in tickers_batch}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                valid_tickers.append(result)
    
    return valid_tickers

def discover_all_tradeable_lse_tickers():
    """
    Main function to discover all tradeable LSE tickers.
    """
    print("=" * 80)
    print("DISCOVERING ALL LSE TICKERS")
    print("=" * 80)
    
    # Generate all potential tickers
    potential_tickers = get_all_lse_tickers()
    
    print(f"Testing {len(potential_tickers)} potential tickers for validity...")
    print("This may take 10-15 minutes...")
    
    # Test in batches to avoid overwhelming the API
    batch_size = 200
    valid_tickers = []
    
    for i in range(0, len(potential_tickers), batch_size):
        batch = potential_tickers[i:i+batch_size]
        print(f"Testing batch {i//batch_size + 1}/{(len(potential_tickers)-1)//batch_size + 1} ({len(batch)} tickers)...")
        
        batch_valid = validate_tickers_batch(batch)
        valid_tickers.extend(batch_valid)
        
        print(f"Found {len(batch_valid)} valid tickers in this batch (Total so far: {len(valid_tickers)})")
        
        # Add small delay between batches to be respectful to the API
        time.sleep(1)
    
    print(f"\nDiscovery complete! Found {len(valid_tickers)} tradeable LSE tickers")
    
    # Save the discovered tickers for future use
    with open(f"discovered_lse_tickers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
        for ticker in sorted(valid_tickers):
            f.write(f"{ticker}\n")
    
    print(f"Saved discovered tickers to file for future reference")
    return valid_tickers

def load_discovered_tickers():
    """
    Load previously discovered tickers from file if available.
    """
    # Look for the most recent discovered tickers file
    ticker_files = glob.glob("discovered_lse_tickers_*.txt")
    if not ticker_files:
        return None
    
    # Get the most recent file
    latest_file = max(ticker_files)
    print(f"Found previous ticker discovery file: {latest_file}")
    
    try:
        with open(latest_file, 'r') as f:
            tickers = [line.strip() for line in f.readlines() if line.strip()]
        print(f"Loaded {len(tickers)} previously discovered tickers")
        return tickers
    except Exception as e:
        print(f"Error loading ticker file: {e}")
        return None

# Fallback list of major LSE tickers in case discovery fails
FALLBACK_LSE_TICKERS = [
    # FTSE 100 major components
    "SHEL.L", "AZN.L", "ULVR.L", "ASML.L", "RELX.L", "BP.L", "GSK.L", "DGE.L",
    "VOD.L", "NG.L", "BATS.L", "LLOY.L", "BARC.L", "RR.L", "RIO.L", "BHP.L",
    "HSBA.L", "CPG.L", "NWG.L", "GLEN.L", "AAL.L", "PRU.L", "LSEG.L", "BT-A.L",
    "IAG.L", "CRH.L", "EXPN.L", "FLTR.L", "FRES.L", "STAN.L", "LAND.L", "SPX.L",
    "WTB.L", "ENT.L", "SBRY.L", "SSE.L", "TSCO.L", "MNDI.L", "NXT.L", "CCH.L",
    
    # ETFs and popular investment instruments
    "VUSA.L", "VMID.L", "VEVE.L", "VFEM.L", "VJPN.L", "VEUR.L", "VGOV.L",
    "ISF.L", "IUSA.L", "IUKD.L", "IDEM.L", "IEVL.L", "IGOV.L", "IBTM.L",
    "TQQQ.L", "SQQQ.L", "QQQ3.L", "EQQQ.L", "3USL.L", "3USS.L",
    
    # Bonds and Fixed Income
    "GILT.L", "GILD.L", "GLTA.L", "GLTB.L", "GLTL.L", "GLTS.L",
    
    # Commodities
    "GOLD.L", "PHAU.L", "SGLN.L", "GBSS.L", "SILV.L", "PSLV.L", "PHYS.L",
    
    # Currency
    "GBPU.L", "EURU.L", "JPYU.L", "CHFU.L",
    
    # UK Banks and Financial
    "LLOY.L", "BARC.L", "NWG.L", "HSBA.L", "STAN.L", "CBG.L",
    
    # UK Utilities
    "SSE.L", "UU.L", "SVT.L", "NG.L", "CNE.L", "PNN.L",
    
    # UK REITs
    "LAND.L", "SGRO.L", "BLND.L", "BBOX.L", "DLAR.L", "EPIC.L", "FCIT.L",
    
    # Technology
    "AUTO.L", "SAGE.L", "PSON.L", "AVV.L", "MICRO.L",
    
    # Consumer
    "TSCO.L", "SBRY.L", "MKS.L", "ULVR.L", "RB.L", "DGE.L", "CCH.L"
]

def download_ticker_data(ticker, start_date, end_date):
    """Download and clean data for a single ticker."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return None, f"{ticker}: No data available"
        
        # Handle multi-level columns
        if data.columns.nlevels > 1:
            data.columns = data.columns.get_level_values(0)
        
        # Check for required columns
        if 'Close' not in data.columns:
            return None, f"{ticker}: No 'Close' column"
        
        # Remove rows with NaN close prices
        data = data.dropna(subset=['Close'])
        
        # Check minimum trading days
        if len(data) < MIN_TRADING_DAYS:
            return None, f"{ticker}: Insufficient data ({len(data)} days, need {MIN_TRADING_DAYS})"
        
        return data[['Close']], None
        
    except Exception as e:
        return None, f"{ticker}: Error downloading - {str(e)}"

def calculate_portfolio_metrics(returns_series):
    """Calculate portfolio performance metrics."""
    if len(returns_series) == 0 or returns_series.std() == 0:
        return {
            'total_return': 0,
            'cagr': 0,
            'volatility': 0,
            'sharpe': 0,
            'sortino': 0,
            'max_drawdown': 0,
            'calmar': 0
        }
    
    # Basic returns
    total_return = (1 + returns_series).prod() - 1
    years = len(returns_series) / 252
    cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
    
    # Risk metrics
    volatility = returns_series.std() * np.sqrt(252)
    sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252)
    
    # Sortino ratio
    downside_returns = returns_series[returns_series < 0]
    sortino = returns_series.mean() / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 and downside_returns.std() > 0 else 0
    
    # Maximum drawdown
    cumulative = (1 + returns_series).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdowns = (cumulative - rolling_max) / rolling_max
    max_drawdown = abs(drawdowns.min())
    
    # Calmar ratio
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    
    return {
        'total_return': total_return,
        'cagr': cagr,
        'volatility': volatility,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'calmar': calmar
    }

def backtest_portfolio(tickers, weights, price_data, rebalance_freq='M'):
    """Backtest a portfolio with given tickers and weights."""
    # Get common date range
    common_dates = price_data[tickers[0]].index
    for ticker in tickers[1:]:
        common_dates = common_dates.intersection(price_data[ticker].index)
    
    if len(common_dates) < MIN_TRADING_DAYS:
        return None
    
    # Create price matrix
    prices = pd.DataFrame()
    for ticker in tickers:
        prices[ticker] = price_data[ticker].loc[common_dates, 'Close']
    
    # Calculate returns
    returns = prices.pct_change().dropna()
    
    if rebalance_freq == 'M':
        # Monthly rebalancing
        monthly_returns = []
        for month_end in returns.resample('M').last().index:
            month_data = returns[returns.index <= month_end]
            if len(month_data) == 0:
                continue
            
            # Get the last month's returns
            if len(monthly_returns) == 0:
                # First month - use all data up to month end
                month_returns = month_data
            else:
                # Subsequent months - use data from last rebalance
                last_rebalance = returns.resample('M').last().index[len(monthly_returns)-1]
                month_returns = returns[(returns.index > last_rebalance) & (returns.index <= month_end)]
            
            if len(month_returns) > 0:
                # Calculate weighted portfolio return for this period
                portfolio_returns = (month_returns * weights).sum(axis=1)
                monthly_returns.extend(portfolio_returns.tolist())
    else:
        # No rebalancing - just weight the daily returns
        portfolio_returns = (returns * weights).sum(axis=1)
        monthly_returns = portfolio_returns.tolist()
    
    portfolio_returns_series = pd.Series(monthly_returns)
    return calculate_portfolio_metrics(portfolio_returns_series)

def test_portfolio_combination(combination_data):
    """Test a specific portfolio combination."""
    tickers, weights, price_data = combination_data
    
    try:
        metrics = backtest_portfolio(tickers, weights, price_data, REBALANCE_FREQUENCY)
        if metrics is None:
            return None
        
        return {
            'tickers': tickers,
            'weights': weights,
            **metrics
        }
    except Exception as e:
        print(f"Error testing {tickers}: {e}")
        return None

def main():
    print("=" * 80)
    print("LSE Portfolio Optimizer - Finding Optimal 2-3 Stock Portfolios")
    print("=" * 80)
    print(f"Core ticker: {CORE_TICKER} (Weight: {CORE_WEIGHT:.1%})")
    print(f"Analysis period: {START_DATE} to {END_DATE or 'Present'}")
    print(f"Rebalancing: {REBALANCE_FREQUENCY}")
    
    # Check command line arguments for discovery mode
    use_discovery = True
    if len(sys.argv) > 1 and sys.argv[1].lower() in ['--fallback', '-f', '--fast']:
        use_discovery = False
        print("Using fallback ticker list (faster execution)")
    
    # Get LSE tickers
    if use_discovery:
        # First try to load previously discovered tickers
        lse_tickers = load_discovered_tickers()
        
        if lse_tickers is None:
            try:
                print("No previous ticker discovery found. Starting fresh discovery...")
                print("Attempting to discover ALL LSE tickers...")
                print("This comprehensive discovery will take 10-15 minutes but finds everything tradeable...")
                print("(Use --fallback flag to skip discovery and use curated list for faster testing)")
                lse_tickers = discover_all_tradeable_lse_tickers()
                print(f"Successfully discovered {len(lse_tickers)} LSE tickers!")
            except Exception as e:
                print(f"Error during ticker discovery: {e}")
                print("Falling back to curated list...")
                lse_tickers = FALLBACK_LSE_TICKERS
        else:
            print("Using previously discovered tickers (delete discovery files to re-run discovery)")
    else:
        print("Using curated fallback list of major LSE tickers...")
        lse_tickers = FALLBACK_LSE_TICKERS
    
    print(f"Will test {len(lse_tickers)} LSE tickers for portfolio optimization...")
    
    # Download data for all tickers
    print("\nDownloading detailed price data for analysis...")
    price_data = {}
    failed_tickers = []
    
    # Always include core ticker
    all_tickers = [CORE_TICKER] + [t for t in lse_tickers if t != CORE_TICKER]
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_ticker_data, ticker, START_DATE, END_DATE): ticker 
                  for ticker in all_tickers}
        
        for future in as_completed(futures):
            ticker = futures[future]
            data, error = future.result()
            
            if data is not None:
                price_data[ticker] = data
                print(f"✓ {ticker}: {len(data)} trading days")
            else:
                failed_tickers.append(ticker)
                print(f"✗ {error}")
    
    print(f"\nSuccessfully downloaded data for {len(price_data)} tickers")
    print(f"Failed to download data for {len(failed_tickers)} tickers")
    
    if CORE_TICKER not in price_data:
        print(f"ERROR: Core ticker {CORE_TICKER} data not available!")
        return
    
    # Remove core ticker from the list of other tickers to test
    other_tickers = [t for t in price_data.keys() if t != CORE_TICKER]
    print(f"Will test combinations with {len(other_tickers)} other tickers")
    
    # Generate portfolio combinations
    results_2_stock = []
    results_3_stock = []
    
    # 2-stock portfolios: LQQ3 (66%) + Other (34%)
    print(f"\nTesting 2-stock portfolios...")
    combinations_2 = []
    for other_ticker in other_tickers:
        tickers = [CORE_TICKER, other_ticker]
        weights = [CORE_WEIGHT, 1 - CORE_WEIGHT]
        combinations_2.append((tickers, weights, price_data))
    
    # Test 2-stock combinations
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(test_portfolio_combination, combo) for combo in combinations_2]
        
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result is not None:
                results_2_stock.append(result)
            
            if (i + 1) % 50 == 0:
                print(f"Completed {i + 1}/{len(combinations_2)} 2-stock combinations")
    
    # 3-stock portfolios: LQQ3 (66%) + Other1 (17%) + Other2 (17%)
    print(f"\nTesting 3-stock portfolios...")
    combinations_3 = []
    remaining_weight = 1 - CORE_WEIGHT
    equal_weight = remaining_weight / 2
    
    for i, ticker1 in enumerate(other_tickers):
        for ticker2 in other_tickers[i+1:]:  # Avoid duplicates
            tickers = [CORE_TICKER, ticker1, ticker2]
            weights = [CORE_WEIGHT, equal_weight, equal_weight]
            combinations_3.append((tickers, weights, price_data))
    
    print(f"Will test {len(combinations_3)} 3-stock combinations")
    
    # Test 3-stock combinations in batches to avoid memory issues
    batch_size = 500
    for batch_start in range(0, len(combinations_3), batch_size):
        batch_end = min(batch_start + batch_size, len(combinations_3))
        batch = combinations_3[batch_start:batch_end]
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(test_portfolio_combination, combo) for combo in batch]
            
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results_3_stock.append(result)
        
        print(f"Completed {batch_end}/{len(combinations_3)} 3-stock combinations")
    
    # Analyze results
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    # Top 10 2-stock portfolios
    if results_2_stock:
        df_2_stock = pd.DataFrame(results_2_stock)
        df_2_stock = df_2_stock.sort_values('calmar', ascending=False)
        
        print(f"\nTOP 10 TWO-STOCK PORTFOLIOS (by Calmar Ratio):")
        print("-" * 60)
        for i, row in df_2_stock.head(10).iterrows():
            tickers_str = " + ".join([f"{t} ({w:.1%})" for t, w in zip(row['tickers'], row['weights'])])
            print(f"{i+1:2d}. {tickers_str}")
            print(f"    Calmar: {row['calmar']:.3f} | CAGR: {row['cagr']:.1%} | Max DD: {row['max_drawdown']:.1%} | Sharpe: {row['sharpe']:.2f}")
        
        # Save 2-stock results
        df_2_stock_save = df_2_stock.copy()
        df_2_stock_save['ticker_1'] = df_2_stock_save['tickers'].apply(lambda x: x[0])
        df_2_stock_save['ticker_2'] = df_2_stock_save['tickers'].apply(lambda x: x[1])
        df_2_stock_save['weight_1'] = df_2_stock_save['weights'].apply(lambda x: x[0])
        df_2_stock_save['weight_2'] = df_2_stock_save['weights'].apply(lambda x: x[1])
        df_2_stock_save = df_2_stock_save.drop(['tickers', 'weights'], axis=1)
        df_2_stock_save.to_csv(f"lse_2stock_portfolio_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    # Top 10 3-stock portfolios
    if results_3_stock:
        df_3_stock = pd.DataFrame(results_3_stock)
        df_3_stock = df_3_stock.sort_values('calmar', ascending=False)
        
        print(f"\nTOP 10 THREE-STOCK PORTFOLIOS (by Calmar Ratio):")
        print("-" * 80)
        for i, row in df_3_stock.head(10).iterrows():
            tickers_str = " + ".join([f"{t} ({w:.1%})" for t, w in zip(row['tickers'], row['weights'])])
            print(f"{i+1:2d}. {tickers_str}")
            print(f"    Calmar: {row['calmar']:.3f} | CAGR: {row['cagr']:.1%} | Max DD: {row['max_drawdown']:.1%} | Sharpe: {row['sharpe']:.2f}")
        
        # Save 3-stock results
        df_3_stock_save = df_3_stock.copy()
        df_3_stock_save['ticker_1'] = df_3_stock_save['tickers'].apply(lambda x: x[0])
        df_3_stock_save['ticker_2'] = df_3_stock_save['tickers'].apply(lambda x: x[1])
        df_3_stock_save['ticker_3'] = df_3_stock_save['tickers'].apply(lambda x: x[2])
        df_3_stock_save['weight_1'] = df_3_stock_save['weights'].apply(lambda x: x[0])
        df_3_stock_save['weight_2'] = df_3_stock_save['weights'].apply(lambda x: x[1])
        df_3_stock_save['weight_3'] = df_3_stock_save['weights'].apply(lambda x: x[2])
        df_3_stock_save = df_3_stock_save.drop(['tickers', 'weights'], axis=1)
        df_3_stock_save.to_csv(f"lse_3stock_portfolio_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
    
    # Compare best of each
    print(f"\n" + "=" * 80)
    print("BEST PORTFOLIO COMPARISON")
    print("=" * 80)
    
    if results_2_stock and results_3_stock:
        best_2 = df_2_stock.iloc[0]
        best_3 = df_3_stock.iloc[0]
        
        print("BEST 2-STOCK PORTFOLIO:")
        tickers_str = " + ".join([f"{t} ({w:.1%})" for t, w in zip(best_2['tickers'], best_2['weights'])])
        print(f"Portfolio: {tickers_str}")
        print(f"Calmar Ratio: {best_2['calmar']:.3f}")
        print(f"CAGR: {best_2['cagr']:.1%}")
        print(f"Max Drawdown: {best_2['max_drawdown']:.1%}")
        print(f"Sharpe Ratio: {best_2['sharpe']:.2f}")
        print(f"Volatility: {best_2['volatility']:.1%}")
        
        print("\nBEST 3-STOCK PORTFOLIO:")
        tickers_str = " + ".join([f"{t} ({w:.1%})" for t, w in zip(best_3['tickers'], best_3['weights'])])
        print(f"Portfolio: {tickers_str}")
        print(f"Calmar Ratio: {best_3['calmar']:.3f}")
        print(f"CAGR: {best_3['cagr']:.1%}")
        print(f"Max Drawdown: {best_3['max_drawdown']:.1%}")
        print(f"Sharpe Ratio: {best_3['sharpe']:.2f}")
        print(f"Volatility: {best_3['volatility']:.1%}")
        
        print(f"\nWINNER: {'3-stock' if best_3['calmar'] > best_2['calmar'] else '2-stock'} portfolio")
    
    # LQQ3 standalone performance for comparison
    print(f"\n" + "=" * 80)
    print("LQQ3 STANDALONE PERFORMANCE (for comparison)")
    print("=" * 80)
    
    lqq3_metrics = backtest_portfolio([CORE_TICKER], [1.0], price_data, REBALANCE_FREQUENCY)
    if lqq3_metrics:
        print(f"CAGR: {lqq3_metrics['cagr']:.1%}")
        print(f"Max Drawdown: {lqq3_metrics['max_drawdown']:.1%}")
        print(f"Calmar Ratio: {lqq3_metrics['calmar']:.3f}")
        print(f"Sharpe Ratio: {lqq3_metrics['sharpe']:.2f}")
        print(f"Volatility: {lqq3_metrics['volatility']:.1%}")
    
    print(f"\nAnalysis complete! Results saved to CSV files.")
    print(f"Tested {len(results_2_stock)} 2-stock and {len(results_3_stock)} 3-stock portfolios.")

if __name__ == "__main__":
    main()
