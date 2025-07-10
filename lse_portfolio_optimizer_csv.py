#!/usr/bin/env python3
"""
LSE Portfolio Optimizer using official LSE ticker list
Reads all LSE tickers from All_LSE.csv and finds optimal 2-3 stock portfolios with LQQ3.
Optimizes for Calmar ratio (CAGR / Max Drawdown).
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import itertools
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import time
warnings.filterwarnings('ignore')

# --- Configuration ---
CORE_TICKER = "LQQ3.L"
CORE_WEIGHT = 0.66  # 66% allocation to LQQ3
START_DATE = "2018-01-01"  # Start date for analysis
INITIAL_CAPITAL = 100000
MIN_TRADING_DAYS = 252 * 3  # Minimum 3 years of data (more stringent)
REBALANCE_FREQUENCY = 'M'  # Monthly rebalancing
MAX_WORKERS = 10  # Parallel download workers
BATCH_SIZE = 100  # Process tickers in batches to manage memory

# Asset types to include (focus on more stable instruments)
INCLUDE_ASSET_TYPES = [
    'SHRS',  # Shares (regular stocks)
    'ETFS',  # ETFs
    # 'ETNS',  # ETNs (like LQQ3) - disabled for now due to extreme leverage
    'OTHR',  # Other equity-like instruments
    # 'BOND',  # Bonds (uncomment if you want bonds)
    # 'SFPS',  # Structured Finance Products (uncomment if wanted)
]

def load_lse_tickers(csv_file="All_LSE.csv"):
    """Load LSE tickers from the CSV file."""
    try:
        df = pd.read_csv(csv_file)
        print(f"Loaded {len(df)} total instruments from {csv_file}")
        
        # Filter by asset types we want
        filtered_df = df[df['MiFIR Identifier Code'].isin(INCLUDE_ASSET_TYPES)].copy()
        print(f"Filtered to {len(filtered_df)} instruments of types: {INCLUDE_ASSET_TYPES}")
        
        # Add .L suffix for yfinance
        tickers = [ticker + ".L" for ticker in filtered_df['Ticker'].tolist()]
        
        # Create a mapping of ticker to instrument info
        ticker_info = {}
        for _, row in filtered_df.iterrows():
            ticker_with_suffix = row['Ticker'] + ".L"
            ticker_info[ticker_with_suffix] = {
                'name': row['Instrument Name'],
                'issuer': row['Issuer Name'], 
                'type': row['MiFIR Identifier Description']
            }
        
        print(f"Asset type breakdown:")
        type_counts = filtered_df['MiFIR Identifier Description'].value_counts()
        for asset_type, count in type_counts.items():
            print(f"  {asset_type}: {count}")
        
        return tickers, ticker_info
        
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return [], {}

def download_ticker_data(ticker):
    """Download and validate data for a single ticker."""
    try:
        # Try different approaches for downloading data
        data = None
        
        # Method 1: Standard download with start date
        try:
            data = yf.download(ticker, start=START_DATE, progress=False, auto_adjust=True, 
                             threads=False, group_by=None)
        except:
            pass
        
        # Method 2: If first method fails, try with period instead
        if data is None or data.empty:
            try:
                data = yf.download(ticker, period="max", progress=False, auto_adjust=True,
                                 threads=False, group_by=None)
            except:
                pass
        
        # Method 3: Try with basic parameters
        if data is None or data.empty:
            try:
                data = yf.download(ticker, start=START_DATE, progress=False)
            except:
                pass
        
        if data is None or data.empty:
            return None, f"No data available"
        
        # Handle multi-level columns properly
        if hasattr(data.columns, 'nlevels') and data.columns.nlevels > 1:
            # For multi-level columns, get the second level (Price type) and flatten
            if len(data.columns.levels) >= 2:
                data.columns = data.columns.get_level_values(1)
            else:
                data.columns = data.columns.get_level_values(0)
        
        # Debug: Check what columns we have now
        available_columns = list(data.columns)
        
        # Check for required columns (try different variations)
        close_col = None
        for col in ['Close', 'close', 'CLOSE', 'Adj Close']:
            if col in available_columns:
                close_col = col
                break
        
        if close_col is None:
            return None, f"No Close column found. Available: {available_columns}"
        
        # Remove rows with NaN close prices
        data = data.dropna(subset=[close_col])
        
        # Filter data to our date range if we downloaded max period
        if START_DATE:
            data = data[data.index >= START_DATE]
        
        # Check minimum trading days and basic data quality
        if len(data) < MIN_TRADING_DAYS:
            return None, f"Insufficient data ({len(data)} days, need {MIN_TRADING_DAYS})"
        
        # Check for reasonable price data (avoid obvious errors)
        close_prices = data[close_col]
        if close_prices.min() <= 0:
            return None, f"Invalid prices (negative/zero)"
        
        # Check for extreme price ranges (might indicate data errors or highly leveraged products)
        price_ratio = close_prices.max() / close_prices.min()
        if price_ratio > 1000:  # Much stricter filter
            return None, f"Suspicious price range (ratio: {price_ratio:.0f})"
        
        # Check that prices actually change (not all the same)
        if close_prices.nunique() < 10:  # More stringent requirement
            return None, f"Price data lacks variation ({close_prices.nunique()} unique values)"
        
        # Check for reasonable daily volatility (filter out extreme leveraged products)
        returns = close_prices.pct_change().dropna()
        if len(returns) > 0:
            daily_vol = returns.std()
            max_daily_return = abs(returns).max()
            
            # Filter out products with extreme daily volatility
            if daily_vol > 0.25:  # More than 25% daily standard deviation
                return None, f"Excessive volatility (daily std: {daily_vol:.1%})"
            
            # Filter out products with extreme single-day moves
            if max_daily_return > 0.50:  # More than 50% single day move
                return None, f"Extreme daily moves (max: {max_daily_return:.1%})"
        
        # Require minimum data coverage since our start date
        data_start_date = data.index[0]
        required_start = pd.to_datetime(START_DATE)
        if data_start_date > required_start + pd.DateOffset(years=1):
            return None, f"Insufficient history (starts {data_start_date.date()}, need {required_start.date()})"
        
        # Filter out very high-priced instruments (likely leveraged products)
        avg_price = close_prices.mean()
        if avg_price > 10000:  # Average price above 10,000 suggests leveraged product
            return None, f"High-priced instrument (avg: {avg_price:.0f}, likely leveraged)"
        
        # Return data with standardized column name
        result_data = data[[close_col]].copy()
        result_data.columns = ['Close']  # Standardize column name
        return result_data, None
        
    except Exception as e:
        return None, f"Download error: {str(e)[:50]}"

def calculate_portfolio_metrics(returns_series):
    """Calculate portfolio performance metrics."""
    if len(returns_series) == 0 or returns_series.std() == 0:
        return None
    
    # Sanity check on returns
    if abs(returns_series.mean()) > 0.5:  # More than 50% average daily return is unrealistic
        return None
    
    if returns_series.std() > 0.5:  # More than 50% daily volatility is unrealistic
        return None
    
    # Basic returns
    total_return = (1 + returns_series).prod() - 1
    years = len(returns_series) / 252
    cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
    
    # Sanity check on CAGR
    if abs(cagr) > 2.0:  # More than 200% CAGR is unrealistic for portfolio analysis
        return None
    
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
    
    # Sanity check on drawdown
    if max_drawdown > 0.95:  # More than 95% drawdown is unrealistic
        return None
    
    # Calmar ratio
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    
    # Sanity check on Calmar ratio
    if abs(calmar) > 10:  # Calmar ratio above 10 is suspicious
        return None
    
    return {
        'total_return': total_return,
        'cagr': cagr,
        'volatility': volatility,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'calmar': calmar
    }

def backtest_portfolio(tickers, weights, price_data):
    """Backtest a portfolio with given tickers and weights."""
    try:
        # Get common date range
        common_dates = price_data[tickers[0]].index
        for ticker in tickers[1:]:
            common_dates = common_dates.intersection(price_data[ticker].index)
        
        if len(common_dates) < MIN_TRADING_DAYS:
            return None
        
        # Create returns matrix
        returns_df = pd.DataFrame()
        for ticker in tickers:
            returns_df[ticker] = price_data[ticker].loc[common_dates, 'Close'].pct_change()
        
        returns_df = returns_df.dropna()
        
        if len(returns_df) < MIN_TRADING_DAYS:
            return None
        
        # Monthly rebalancing
        portfolio_returns = []
        monthly_ends = returns_df.resample('M').last().index
        
        for i, month_end in enumerate(monthly_ends):
            if i == 0:
                # First month - use all data up to month end
                month_returns = returns_df[returns_df.index <= month_end]
            else:
                # Subsequent months - data from last rebalance to current month end
                last_rebalance = monthly_ends[i-1]
                month_returns = returns_df[(returns_df.index > last_rebalance) & (returns_df.index <= month_end)]
            
            if len(month_returns) > 0:
                # Calculate weighted portfolio returns for this period
                period_returns = (month_returns * weights).sum(axis=1)
                portfolio_returns.extend(period_returns.tolist())
        
        if len(portfolio_returns) == 0:
            return None
            
        return calculate_portfolio_metrics(pd.Series(portfolio_returns))
        
    except Exception as e:
        return None

def test_portfolio_batch(combinations):
    """Test a batch of portfolio combinations."""
    results = []
    for tickers, weights, price_data in combinations:
        metrics = backtest_portfolio(tickers, weights, price_data)
        if metrics:
            results.append({
                'tickers': tickers,
                'weights': weights,
                **metrics
            })
    return results

def main():
    print("=" * 80)
    print("LSE PORTFOLIO OPTIMIZER - Using Official LSE Ticker List")
    print("=" * 80)
    print(f"Core ticker: {CORE_TICKER} (Weight: {CORE_WEIGHT:.1%})")
    print(f"Analysis period: {START_DATE} to present")
    print(f"Asset types included: {', '.join(INCLUDE_ASSET_TYPES)}")
    print(f"Minimum trading days: {MIN_TRADING_DAYS}")
    
    # Load LSE tickers from CSV
    print("\nLoading LSE tickers from All_LSE.csv...")
    all_tickers, ticker_info = load_lse_tickers()
    
    if not all_tickers:
        print("ERROR: No tickers loaded from CSV!")
        return
    
    if CORE_TICKER not in all_tickers:
        print(f"WARNING: Core ticker {CORE_TICKER} not in the LSE list, adding it...")
        all_tickers.insert(0, CORE_TICKER)
    
    print(f"Will test {len(all_tickers)} LSE tickers")
    
    # First, validate the core ticker specifically
    print(f"\nValidating core ticker {CORE_TICKER}...")
    core_data, core_error = download_ticker_data(CORE_TICKER)
    if core_data is None:
        print(f"CRITICAL ERROR: Core ticker {CORE_TICKER} failed to download!")
        print(f"Error: {core_error}")
        print("Cannot proceed without core ticker data. Please check:")
        print("1. Ticker symbol is correct")
        print("2. Internet connection is working") 
        print("3. yfinance API is accessible")
        return
    else:
        print(f"✓ Core ticker {CORE_TICKER} validated: {len(core_data)} trading days")
    
    # Download data for all tickers in batches
    print(f"\nDownloading price data using {MAX_WORKERS} workers...")
    price_data = {CORE_TICKER: core_data}  # Start with validated core ticker
    failed_count = 0
    
    # Remove core ticker from download list since we already have it
    tickers_to_download = [t for t in all_tickers if t != CORE_TICKER]
    
    # Process in batches to manage memory
    for batch_start in range(0, len(tickers_to_download), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(tickers_to_download))
        batch_tickers = tickers_to_download[batch_start:batch_end]
        
        print(f"Processing batch {batch_start//BATCH_SIZE + 1}/{(len(tickers_to_download)-1)//BATCH_SIZE + 1} ({len(batch_tickers)} tickers)")
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(download_ticker_data, ticker): ticker for ticker in batch_tickers}
            
            for future in as_completed(futures):
                ticker = futures[future]
                data, error = future.result()
                
                if data is not None:
                    price_data[ticker] = data
                    if ticker in ticker_info:
                        asset_type = ticker_info[ticker]['type']
                        print(f"✓ {ticker} ({asset_type})")
                    else:
                        print(f"✓ {ticker}")
                else:
                    failed_count += 1
                    if ticker == CORE_TICKER:
                        print(f"✗ {ticker}: {error} [CRITICAL - CORE TICKER FAILED]")
                    # Only show first few failures to avoid spam
                    elif failed_count <= 10:
                        print(f"✗ {ticker}: {error}")
        
        # Brief pause between batches
        time.sleep(0.5)
    
    print(f"\nDownload complete:")
    print(f"✓ Valid tickers: {len(price_data)} (including {CORE_TICKER})")
    print(f"✗ Failed tickers: {failed_count}")
    
    # Core ticker should already be validated, but double-check
    if CORE_TICKER not in price_data:
        print(f"UNEXPECTED ERROR: Core ticker {CORE_TICKER} missing from price data!")
        return
    
    # Remove core ticker from other tickers list
    other_tickers = [t for t in price_data.keys() if t != CORE_TICKER]
    print(f"Will test combinations with {len(other_tickers)} other tickers")
    
    if len(other_tickers) == 0:
        print("ERROR: No other valid tickers to combine with core ticker!")
        return
    
    # Test 2-stock portfolios
    print(f"\nTesting 2-stock portfolios...")
    results_2_stock = []
    
    combinations_2 = []
    for other_ticker in other_tickers:
        tickers = [CORE_TICKER, other_ticker]
        weights = [CORE_WEIGHT, 1 - CORE_WEIGHT]
        combinations_2.append((tickers, weights, price_data))
    
    # Process 2-stock combinations in batches
    batch_size_2 = 100
    for i in range(0, len(combinations_2), batch_size_2):
        batch = combinations_2[i:i+batch_size_2]
        batch_results = test_portfolio_batch(batch)
        results_2_stock.extend(batch_results)
        
        if (i + batch_size_2) % 500 == 0:
            print(f"Completed {min(i + batch_size_2, len(combinations_2))}/{len(combinations_2)} 2-stock combinations")
    
    print(f"Completed all {len(combinations_2)} 2-stock combinations, found {len(results_2_stock)} valid portfolios")
    
    # Test 3-stock portfolios (limit to top performers to manage computation)
    print(f"\nTesting 3-stock portfolios...")
    
    # Limit 3-stock tests to reasonable number
    max_other_tickers_for_3stock = min(len(other_tickers), 200)  # Limit to avoid excessive computation
    if len(other_tickers) > max_other_tickers_for_3stock:
        print(f"Limiting 3-stock analysis to top {max_other_tickers_for_3stock} tickers by individual performance")
        
        # Quick ranking of individual tickers
        individual_performance = []
        for ticker in other_tickers[:max_other_tickers_for_3stock * 3]:  # Test a subset for ranking
            metrics = backtest_portfolio([ticker], [1.0], price_data)
            if metrics:
                individual_performance.append((ticker, metrics['calmar']))
        
        # Sort by calmar ratio and take top performers
        individual_performance.sort(key=lambda x: x[1], reverse=True)
        limited_other_tickers = [t[0] for t in individual_performance[:max_other_tickers_for_3stock]]
    else:
        limited_other_tickers = other_tickers
    
    print(f"Testing 3-stock combinations with {len(limited_other_tickers)} other tickers")
    
    results_3_stock = []
    remaining_weight = 1 - CORE_WEIGHT
    equal_weight = remaining_weight / 2
    
    combinations_3 = []
    for i, ticker1 in enumerate(limited_other_tickers):
        for ticker2 in limited_other_tickers[i+1:]:
            tickers = [CORE_TICKER, ticker1, ticker2]
            weights = [CORE_WEIGHT, equal_weight, equal_weight]
            combinations_3.append((tickers, weights, price_data))
    
    print(f"Will test {len(combinations_3)} 3-stock combinations")
    
    # Process 3-stock combinations in smaller batches
    batch_size_3 = 50
    for i in range(0, len(combinations_3), batch_size_3):
        batch = combinations_3[i:i+batch_size_3]
        batch_results = test_portfolio_batch(batch)
        results_3_stock.extend(batch_results)
        
        if (i + batch_size_3) % 1000 == 0:
            print(f"Completed {min(i + batch_size_3, len(combinations_3))}/{len(combinations_3)} 3-stock combinations")
    
    print(f"Completed {len(combinations_3)} 3-stock combinations, found {len(results_3_stock)} valid portfolios")
    
    # Analyze and save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    # Best 2-stock portfolios
    if results_2_stock:
        df_2 = pd.DataFrame(results_2_stock).sort_values('calmar', ascending=False)
        
        print(f"\nTOP 10 TWO-STOCK PORTFOLIOS (by Calmar Ratio):")
        print("-" * 100)
        for i, row in df_2.head(10).iterrows():
            portfolio_str = f"{row['tickers'][0]} ({row['weights'][0]:.0%}) + {row['tickers'][1]} ({row['weights'][1]:.0%})"
            
            # Add asset type info if available
            other_ticker = row['tickers'][1]
            if other_ticker in ticker_info:
                asset_type = ticker_info[other_ticker]['type']
                portfolio_str += f" [{asset_type}]"
            
            print(f"{i+1:2d}. {portfolio_str}")
            print(f"    Calmar: {row['calmar']:.3f} | CAGR: {row['cagr']:.1%} | MaxDD: {row['max_drawdown']:.1%} | Sharpe: {row['sharpe']:.2f}")
        
        # Save results
        df_2_save = df_2.copy()
        df_2_save['ticker_1'] = df_2_save['tickers'].str[0]
        df_2_save['ticker_2'] = df_2_save['tickers'].str[1]
        df_2_save['weight_1'] = df_2_save['weights'].str[0]
        df_2_save['weight_2'] = df_2_save['weights'].str[1]
        
        # Add asset type info
        df_2_save['asset_type_2'] = df_2_save['ticker_2'].apply(
            lambda x: ticker_info.get(x, {}).get('type', 'Unknown')
        )
        
        df_2_save = df_2_save.drop(['tickers', 'weights'], axis=1)
        filename_2 = f"lse_2stock_portfolio_results_{timestamp}.csv"
        df_2_save.to_csv(filename_2, index=False)
        print(f"\n2-stock results saved to {filename_2}")
    
    # Best 3-stock portfolios
    if results_3_stock:
        df_3 = pd.DataFrame(results_3_stock).sort_values('calmar', ascending=False)
        
        print(f"\nTOP 10 THREE-STOCK PORTFOLIOS (by Calmar Ratio):")
        print("-" * 120)
        for i, row in df_3.head(10).iterrows():
            portfolio_str = f"{row['tickers'][0]} ({row['weights'][0]:.0%}) + {row['tickers'][1]} ({row['weights'][1]:.0%}) + {row['tickers'][2]} ({row['weights'][2]:.0%})"
            
            # Add asset type info
            other_tickers = row['tickers'][1:3]
            asset_types = []
            for ticker in other_tickers:
                if ticker in ticker_info:
                    asset_types.append(ticker_info[ticker]['type'])
            if asset_types:
                portfolio_str += f" [{', '.join(asset_types)}]"
            
            print(f"{i+1:2d}. {portfolio_str}")
            print(f"    Calmar: {row['calmar']:.3f} | CAGR: {row['cagr']:.1%} | MaxDD: {row['max_drawdown']:.1%} | Sharpe: {row['sharpe']:.2f}")
        
        # Save results
        df_3_save = df_3.copy()
        df_3_save['ticker_1'] = df_3_save['tickers'].str[0]
        df_3_save['ticker_2'] = df_3_save['tickers'].str[1]
        df_3_save['ticker_3'] = df_3_save['tickers'].str[2]
        df_3_save['weight_1'] = df_3_save['weights'].str[0]
        df_3_save['weight_2'] = df_3_save['weights'].str[1]
        df_3_save['weight_3'] = df_3_save['weights'].str[2]
        
        # Add asset type info
        df_3_save['asset_type_2'] = df_3_save['ticker_2'].apply(
            lambda x: ticker_info.get(x, {}).get('type', 'Unknown')
        )
        df_3_save['asset_type_3'] = df_3_save['ticker_3'].apply(
            lambda x: ticker_info.get(x, {}).get('type', 'Unknown')
        )
        
        df_3_save = df_3_save.drop(['tickers', 'weights'], axis=1)
        filename_3 = f"lse_3stock_portfolio_results_{timestamp}.csv"
        df_3_save.to_csv(filename_3, index=False)
        print(f"3-stock results saved to {filename_3}")
    
    # LQQ3 standalone for comparison
    print(f"\n" + "=" * 80)
    print("LQQ3 STANDALONE PERFORMANCE (for comparison)")
    print("=" * 80)
    
    lqq3_metrics = backtest_portfolio([CORE_TICKER], [1.0], price_data)
    if lqq3_metrics:
        print(f"CAGR: {lqq3_metrics['cagr']:.1%}")
        print(f"Max Drawdown: {lqq3_metrics['max_drawdown']:.1%}")
        print(f"Calmar Ratio: {lqq3_metrics['calmar']:.3f}")
        print(f"Sharpe Ratio: {lqq3_metrics['sharpe']:.2f}")
        print(f"Volatility: {lqq3_metrics['volatility']:.1%}")
    
    # Final summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if results_2_stock and results_3_stock:
        best_2_calmar = df_2.iloc[0]['calmar']
        best_3_calmar = df_3.iloc[0]['calmar']
        lqq3_calmar = lqq3_metrics['calmar'] if lqq3_metrics else 0
        
        print(f"Best 2-stock Calmar ratio: {best_2_calmar:.3f}")
        print(f"Best 3-stock Calmar ratio: {best_3_calmar:.3f}")
        print(f"LQQ3 standalone Calmar ratio: {lqq3_calmar:.3f}")
        
        best_overall = max(best_2_calmar, best_3_calmar)
        if best_overall > lqq3_calmar:
            portfolio_type = "3-stock" if best_3_calmar > best_2_calmar else "2-stock"
            improvement = (best_overall / lqq3_calmar - 1) * 100 if lqq3_calmar > 0 else 0
            print(f"\nRecommendation: {portfolio_type} portfolio with {improvement:.1f}% better Calmar ratio than LQQ3 alone")
        else:
            print(f"\nRecommendation: Stick with LQQ3 standalone")
    
    print(f"\nAnalysis complete! Tested {len(price_data)} valid tickers from LSE.")

if __name__ == "__main__":
    main()
