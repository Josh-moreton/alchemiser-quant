#!/usr/bin/env python3
"""
LSE Portfolio Optimizer using official LSE ticker list
Reads all LSE tickers from All_LSE.csv and finds optimal 2-3 stock portfolios with LQQ3.
Optimizes for LOWEST MAXIMUM DRAWDOWN to hedge against LQQ3's volatility.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed # Changed to ProcessPoolExecutor
import warnings
import time
import os
import pickle
warnings.filterwarnings('ignore')

# --- Configuration ---
CORE_TICKER = "LQQ3.L"
CORE_WEIGHT = 0.66  # 66% allocation to LQQ3
# START_DATE is determined by the cached data's range
INITIAL_CAPITAL = 65000
MIN_TRADING_DAYS = 252 * 3  # Minimum 3 years of data
REBALANCE_FREQUENCY = 'Q'  # Quarterly rebalancing
DATA_FOLDER = "lse_ticker_data"  # Cached data folder

# Asset types to include (can be used for filtering later if needed)
INCLUDE_ASSET_TYPES = [
    'SHRS',  # Shares (regular stocks)
    'ETFS',  # ETFs (like LQQ3)
    'ETCS',  # ETCs (Exchange Traded Commodities)
    'OTHR',  # Other equity-like instruments
]

def load_cached_data():
    """Load all cached ticker data and metadata."""
    if not os.path.exists(DATA_FOLDER):
        print(f"ERROR: Data folder '{DATA_FOLDER}' not found!")
        print("Please run the downloader script first to cache the data.")
        return None, None
    
    # Load ticker info
    ticker_info_file = os.path.join(DATA_FOLDER, 'ticker_info.pkl')
    if not os.path.exists(ticker_info_file):
        print(f"ERROR: 'ticker_info.pkl' not found in '{DATA_FOLDER}'!")
        print("Please run the downloader script first.")
        return None, None
        
    with open(ticker_info_file, 'rb') as f:
        ticker_info = pickle.load(f)
    
    # Load all ticker data
    price_data = {}
    cache_files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.pkl') and f != 'ticker_info.pkl']
    
    print(f"Loading {len(cache_files)} cached ticker files...")
    
    for cache_file in cache_files:
        ticker = cache_file.replace('_', '.').replace('.pkl', '')
        ticker_file_path = os.path.join(DATA_FOLDER, cache_file)
        try:
            with open(ticker_file_path, 'rb') as f:
                data = pickle.load(f)
                # Validate data on load
                # Make a special exception to always load the core ticker
                if ticker == CORE_TICKER:
                    if data is not None and not data.empty:
                        price_data[ticker] = data
                    else:
                        # This case should be rare, but good to handle
                        print(f"Warning: Core ticker {CORE_TICKER} file was found but is empty.")
                elif data is not None and not data.empty and len(data) >= MIN_TRADING_DAYS:
                    price_data[ticker] = data
        except Exception as e:
            print(f"Warning: Could not load or validate {ticker}: {e}")
    
    print(f"✓ Loaded {len(price_data)} tickers from cache that meet the minimum trading day requirement (or are the core ticker).")
    return price_data, ticker_info

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
    print("LSE PORTFOLIO OPTIMIZER - Using Pre-Cached Data")
    print("=" * 80)
    print(f"Core ticker: {CORE_TICKER} (Weight: {CORE_WEIGHT:.1%})")
    print(f"Optimization goal: MINIMIZE MAXIMUM DRAWDOWN")
    print(f"Data source: Cached data from '{DATA_FOLDER}/'")
    print(f"Minimum trading days required: {MIN_TRADING_DAYS}")
    
    # Load cached data
    print("\nLoading cached ticker data...")
    price_data, ticker_info = load_cached_data()
    
    if not price_data or not ticker_info:
        print("Could not load data. Exiting.")
        return
    
    # Check if core ticker is available
    if CORE_TICKER not in price_data:
        print(f"ERROR: Core ticker {CORE_TICKER} not found in cached data!")
        return
    
    print(f"✓ Found {len(price_data)} cached tickers including {CORE_TICKER}")
    
    # Show asset type breakdown from cache
    if ticker_info:
        print(f"\nAsset type breakdown in cache:")
        asset_type_counts = {}
        for ticker, info in ticker_info.items():
            if ticker in price_data:  # Only count tickers that loaded successfully
                asset_type = info['type']
                asset_type_counts[asset_type] = asset_type_counts.get(asset_type, 0) + 1
        
        for asset_type, count in asset_type_counts.items():
            print(f"  {asset_type}: {count}")
    
    # Remove core ticker from other tickers list
    other_tickers = [t for t in price_data.keys() if t != CORE_TICKER]
    print(f"\nWill test combinations with {len(other_tickers)} other tickers")
    
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
    
    # Process 2-stock combinations in parallel
    print(f"Will test {len(combinations_2)} 2-stock combinations using multi-processing...")
    batch_size_2 = 100  # How many combinations to send to each process at once
    with ProcessPoolExecutor() as executor:
        futures = []
        for i in range(0, len(combinations_2), batch_size_2):
            batch = combinations_2[i:i+batch_size_2]
            futures.append(executor.submit(test_portfolio_batch, batch))
        
        for i, future in enumerate(as_completed(futures)):
            results_2_stock.extend(future.result())
            if (i + 1) % 5 == 0: # Update progress every 5 batches
                 print(f"Completed {min((i + 1) * batch_size_2, len(combinations_2))}/{len(combinations_2)} 2-stock combinations")

    print(f"Completed all {len(combinations_2)} 2-stock combinations, found {len(results_2_stock)} valid portfolios")
    
    # Test 3-stock portfolios
    print(f"\nTesting 3-stock portfolios...")
    
    print(f"Testing 3-stock combinations with all {len(other_tickers)} other tickers.")
    
    results_3_stock = []
    remaining_weight = 1 - CORE_WEIGHT
    equal_weight = remaining_weight / 2
    
    combinations_3 = []
    for i, ticker1 in enumerate(other_tickers):
        for ticker2 in other_tickers[i+1:]:
            tickers = [CORE_TICKER, ticker1, ticker2]
            weights = [CORE_WEIGHT, equal_weight, equal_weight]
            combinations_3.append((tickers, weights, price_data))
    
    print(f"Will test {len(combinations_3)} 3-stock combinations using multi-processing...")
    
    # Process 3-stock combinations in parallel
    batch_size_3 = 50 # Smaller batches for more frequent progress updates
    with ProcessPoolExecutor() as executor:
        futures = []
        for i in range(0, len(combinations_3), batch_size_3):
            batch = combinations_3[i:i+batch_size_3]
            futures.append(executor.submit(test_portfolio_batch, batch))
        
        for i, future in enumerate(as_completed(futures)):
            results_3_stock.extend(future.result())
            if (i + 1) % 20 == 0: # Update progress every 20 batches
                print(f"Completed {min((i + 1) * batch_size_3, len(combinations_3))}/{len(combinations_3)} 3-stock combinations")

    print(f"Completed {len(combinations_3)} 3-stock combinations, found {len(results_3_stock)} valid portfolios")
    
    # Analyze and save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    # Best 2-stock portfolios
    if results_2_stock:
        df_2 = pd.DataFrame(results_2_stock).sort_values('max_drawdown', ascending=True)  # Sort by LOWEST drawdown
        
        print(f"\nTOP 10 TWO-STOCK PORTFOLIOS (by Lowest Maximum Drawdown):")
        print("-" * 100)
        for i, row in df_2.head(10).iterrows():
            portfolio_str = f"{row['tickers'][0]} ({row['weights'][0]:.0%}) + {row['tickers'][1]} ({row['weights'][1]:.0%})"
            
            # Add asset type info if available
            other_ticker = row['tickers'][1]
            if other_ticker in ticker_info:
                asset_type = ticker_info[other_ticker]['type']
                portfolio_str += f" [{asset_type}]"
            
            print(f"{i+1:2d}. {portfolio_str}")
            print(f"    MaxDD: {row['max_drawdown']:.1%} | CAGR: {row['cagr']:.1%} | Calmar: {row['calmar']:.3f} | Sharpe: {row['sharpe']:.2f}")
        
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
        df_3 = pd.DataFrame(results_3_stock).sort_values('max_drawdown', ascending=True)  # Sort by LOWEST drawdown
        
        print(f"\nTOP 10 THREE-STOCK PORTFOLIOS (by Lowest Maximum Drawdown):")
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
            print(f"    MaxDD: {row['max_drawdown']:.1%} | CAGR: {row['cagr']:.1%} | Calmar: {row['calmar']:.3f} | Sharpe: {row['sharpe']:.2f}")
        
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
        best_2_drawdown = df_2.iloc[0]['max_drawdown']
        best_3_drawdown = df_3.iloc[0]['max_drawdown']
        lqq3_drawdown = lqq3_metrics['max_drawdown'] if lqq3_metrics else 1.0
        
        print(f"Best 2-stock Max Drawdown: {best_2_drawdown:.1%}")
        print(f"Best 3-stock Max Drawdown: {best_3_drawdown:.1%}")
        print(f"LQQ3 standalone Max Drawdown: {lqq3_drawdown:.1%}")
        
        best_overall_drawdown = min(best_2_drawdown, best_3_drawdown)
        if best_overall_drawdown < lqq3_drawdown:
            portfolio_type = "3-stock" if best_3_drawdown < best_2_drawdown else "2-stock"
            improvement = (lqq3_drawdown - best_overall_drawdown) / lqq3_drawdown * 100 if lqq3_drawdown > 0 else 0
            print(f"\nRecommendation: {portfolio_type} portfolio reduces max drawdown by {improvement:.1f}% vs LQQ3 alone")
        else:
            print(f"\nRecommendation: Stick with LQQ3 standalone - diversification doesn't improve drawdown")
    
    print(f"\nAnalysis complete! Tested {len(price_data)} valid tickers from LSE.")

if __name__ == "__main__":
    main()
