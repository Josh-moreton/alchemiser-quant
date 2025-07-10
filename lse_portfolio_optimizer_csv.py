#!/usr/bin/env python3
"""
LSE Portfolio Optimizer using official LSE ticker list
Reads all LSE tickers from All_LSE.csv and finds optimal 3 stock portfolios with LQQ3.
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
FIXED_HEDGE_TICKER = "SGLN.L" # New: Fixed second ticker for 3-stock analysis
# CORE_WEIGHT is now variable: 50%, 60%, 70%
START_DATE = "2015-07-10"  # Fixed start date: 10 years ago from 2025-07-10
INITIAL_CAPITAL = 65000
MIN_TRADING_DAYS = 252 * 10  # Minimum 10 years of data
REBALANCE_FREQUENCY = 'Q'  # Quarterly rebalancing
DATA_FOLDER = "lse_ticker_data"  # Cached data folder

# Asset types to include (can be used for filtering later if needed)
INCLUDE_ASSET_TYPES = [
    'ETFs',
    'ETCs',
    'ETNs',
    'Other equity-like financial instruments',
]

# Expanded curated list for 3-fund portfolio optimization with NASDAQ + Gold
# Strategic focus: Find third assets that complement high-growth tech (LQQ3) + defensive gold (SGLN)
# Goal: High returns + Low drawdown through diversification across uncorrelated asset classes
CURATED_THIRD_TICKERS = [
    
    # === DEFENSIVE BONDS (Negative correlation to stocks, stability during crashes) ===
    # UK Government Bonds - Flight to safety during tech crashes
    'UKGL.L', 'GILS.L', 'IGLT.L', 'UKG5.L', 'GOVT.L', 'INXG.L',
    
    # Global Government Bonds - International diversification 
    'DTLA.L', 'AGGG.L', 'SAGG.L', 'GLTY.L', 'SLVP.L', 'VGOV.L',
    
    # Treasury Bills & Short Duration - Ultimate stability, minimal duration risk
    'GILT.L', 'CSH2.L', 'XGOV.L', 'ERNS.L',
    
    # Corporate Bonds - Higher yield than govts, still defensive
    'CORP.L', 'CBND.L', 'INKM.L', 'HYLD.L', 'SHYG.L', 'SLXX.L',
    
    # === HIGH DIVIDEND INCOME (Steady cash flow, different from growth stocks) ===
    # UK High Dividend - Income focus vs growth focus of NASDAQ
    'VDIV.L', 'HDIV.L', 'UKHD.L', 'UKDV.L', 'DIVI.L',
    
    # Global High Dividend - International income diversification
    'VHYL.L', 'VGHY.L', 'IHYG.L', 'TDIV.L', 'QDIV.L',
    
    # Dividend Aristocrats - Quality dividend growers
    'DQAL.L', 'DGIT.L', 'FCSG.L',
    
    # === VALUE STOCKS (Opposite style to growth-heavy NASDAQ) ===
    # UK Value - Complement to US growth
    'VVAL.L', 'VMID.L', 'UKSC.L', 'FTAL.L',
    
    # Global Value - International value exposure
    'VAVE.L', 'IWVL.L', 'IUVL.L',
    
    # === INTERNATIONAL EQUITY (Geographic diversification from US-heavy NASDAQ) ===
    # European Markets - Different economic cycles
    'VEUR.L', 'HMEU.L', 'VERX.L', 'IEUR.L', 'IEAC.L',
    
    # Japanese Markets - Unique economic dynamics
    'VJPN.L', 'VJPA.L', 'IJPN.L', 'VJPH.L',
    
    # Asia Pacific (ex-Japan) - High growth potential
    'VAPX.L', 'VAPA.L', 'IAPD.L',
    
    # Emerging Markets - Higher growth, different correlations
    'VFEM.L', 'EMIM.L', 'EMAS.L', 'SEMG.L', 'EMDD.L', 'IEMB.L',
    
    # === ALTERNATIVE ASSETS (Low correlation to both stocks and bonds) ===
    # Real Estate - Different return drivers than tech stocks
    'IPRP.L', 'TREI.L', 'UKRE.L', 'EPRA.L', 'IWDP.L', 'REIT.L',
    
    # Infrastructure - Essential services, steady cash flows
    'INFU.L', 'IFRA.L', 'TRIG.L',
    
    # Commodities - Inflation hedge beyond gold
    'RICI.L', 'AIGO.L', 'COIL.L', 'COAL.L', 'WEAT.L', 'SOYB.L',
    
    # === SECTOR ROTATION PLAYS (Non-tech sectors for diversification) ===
    # Healthcare - Defensive growth sector
    'IHLC.L', 'HEAL.L', 'HTEC.L',
    
    # Utilities - Defensive income
    'IUTL.L', 'UTIL.L',
    
    # Consumer Staples - Recession-resistant
    'IUCS.L', 'STAP.L',
    
    # Energy - Inflation hedge, cyclical exposure
    'IENG.L', 'OILG.L',
    
    # Financials - Interest rate beneficiary
    'IFIN.L', 'BANK.L',
    
    # === CURRENCY/INFLATION HEDGES (Protection beyond gold) ===
    # Other Precious Metals
    'PHAU.L', 'PHAG.L', 'PHPT.L', 'SLVP.L',
    
    # Inflation-Protected Bonds
    'INXG.L', 'TIPS.L', 'GILT.L',
    
    # === LOW VOLATILITY/QUALITY (Reduce portfolio volatility) ===
    # Low Volatility Strategies
    'MVOL.L', 'LVOL.L', 'USMV.L',
    
    # Quality Factors
    'QUAL.L', 'IQLT.L', 'WQLT.L',
    
    # Momentum (trend following)
    'MTUM.L', 'IMOM.L',
    
    # === MULTI-ASSET/BALANCED (Built-in diversification) ===
    # Conservative Allocation Funds
    'VCON.L', 'VACP.L', 'VGCP.L',
    
    # Target Date/Lifecycle Funds
    'VTEB.L', 'VTEM.L',
    
]

def validate_ticker_data_quality(ticker, data):
    """Validate ticker data quality by checking for extreme returns."""
    try:
        if data is None or data.empty or 'Close' not in data.columns:
            return False, "No price data"
        
        # Calculate daily returns
        returns = data['Close'].pct_change().dropna()
        
        if len(returns) == 0:
            return False, "No valid returns"
        
        # Check for extreme daily returns (likely data errors)
        max_return = returns.max()
        min_return = returns.min()
        
        # Flag tickers with daily returns > 100% or < -90% as likely data errors
        if max_return > 1.0:  # More than 100% daily gain
            return False, f"Extreme positive return: {max_return:.1%}"
        
        if min_return < -0.90:  # More than 90% daily loss
            return False, f"Extreme negative return: {min_return:.1%}"
        
        # Check for too many extreme returns (>50% moves)
        extreme_returns = returns[(returns > 0.50) | (returns < -0.50)]
        if len(extreme_returns) > len(returns) * 0.01:  # More than 1% of days are extreme
            return False, f"Too many extreme returns: {len(extreme_returns)}/{len(returns)}"
        
        return True, "Valid"
    except Exception as e:
        return False, f"Error validating data: {str(e)}"

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
    
    data_quality_issues = []
    
    for cache_file in cache_files:
        ticker = cache_file.replace('_', '.').replace('.pkl', '')
        ticker_file_path = os.path.join(DATA_FOLDER, cache_file)
        try:
            with open(ticker_file_path, 'rb') as f:
                data = pickle.load(f)
                
                # Make a special exception to always load the core ticker
                if ticker == CORE_TICKER:
                    if data is not None and not data.empty:
                        price_data[ticker] = data
                    else:
                        print(f"Warning: Core ticker {CORE_TICKER} file was found but is empty.")
                elif data is not None and not data.empty and len(data) >= MIN_TRADING_DAYS:
                    price_data[ticker] = data
        except Exception as e:
            print(f"Warning: Could not load or validate {ticker}: {e}")
    
    print(f"✓ Loaded {len(price_data)} tickers from cache that meet the minimum trading day requirement.")
    
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
    
    # Sanity check on CAGR - filter out unrealistic results
    if abs(cagr) > 0.5:  # More than 50% CAGR is unrealistic for our analysis
        return None
    
    # Risk metrics
    volatility = returns_series.std() * np.sqrt(252)
    sharpe = returns_series.mean() / returns_series.std() * np.sqrt(252)
    
    # Sortino ratio
    downside_returns = returns_series[returns_series < 0]
    downside_deviation_period = downside_returns.std()
    sortino = returns_series.mean() / downside_deviation_period * np.sqrt(252) if len(downside_returns) > 0 and downside_deviation_period > 0 else 0

    # Downside Protection Ratio (DPR)
    downside_deviation_annual = downside_deviation_period * np.sqrt(252)
    dpr = cagr / downside_deviation_annual if downside_deviation_annual > 0 else 0
    
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
        'dpr': dpr,
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

def debug_backtest_portfolio(tickers, weights, price_data):
    """Debug version of backtest_portfolio to see what's going wrong."""
    try:
        print(f"\n=== DEBUG: Testing {tickers} with weights {weights} ===")
        
        # Get common date range
        common_dates = price_data[tickers[0]].index
        for ticker in tickers[1:]:
            common_dates = common_dates.intersection(price_data[ticker].index)
        
        print(f"Common date range: {common_dates[0]} to {common_dates[-1]} ({len(common_dates)} days)")
        
        if len(common_dates) < MIN_TRADING_DAYS:
            print(f"Not enough data: {len(common_dates)} < {MIN_TRADING_DAYS}")
            return None
        
        # Create returns matrix
        returns_df = pd.DataFrame()
        for ticker in tickers:
            returns_df[ticker] = price_data[ticker].loc[common_dates, 'Close'].pct_change()
            print(f"{ticker} sample prices: {price_data[ticker].loc[common_dates, 'Close'].head(3).values}")
            print(f"{ticker} sample returns: {returns_df[ticker].dropna().head(3).values}")
        
        returns_df = returns_df.dropna()
        print(f"Returns matrix shape after dropna: {returns_df.shape}")
        
        # Check for extreme returns
        for ticker in tickers:
            max_daily_return = returns_df[ticker].max()
            min_daily_return = returns_df[ticker].min()
            print(f"{ticker} max daily return: {max_daily_return:.4f} ({max_daily_return*100:.2f}%)")
            print(f"{ticker} min daily return: {min_daily_return:.4f} ({min_daily_return*100:.2f}%)")
        
        # Monthly rebalancing
        portfolio_returns = []
        monthly_ends = returns_df.resample('M').last().index
        print(f"Monthly rebalancing points: {len(monthly_ends)}")
        
        for i, month_end in enumerate(monthly_ends[:3]):  # Just first 3 months for debug
            if i == 0:
                month_returns = returns_df[returns_df.index <= month_end]
            else:
                last_rebalance = monthly_ends[i-1]
                month_returns = returns_df[(returns_df.index > last_rebalance) & (returns_df.index <= month_end)]
            
            print(f"Month {i+1}: {len(month_returns)} returns")
            if len(month_returns) > 0:
                period_returns = (month_returns * weights).sum(axis=1)
                print(f"Sample portfolio returns for month {i+1}: {period_returns.head(3).values}")
                portfolio_returns.extend(period_returns.tolist())
        
        print(f"Total portfolio returns collected: {len(portfolio_returns)}")
        if len(portfolio_returns) > 0:
            print(f"Sample portfolio returns: {portfolio_returns[:5]}")
            
        return None  # Don't calculate metrics for debug
        
    except Exception as e:
        print(f"Error in debug: {e}")
        return None

def generate_weight_combinations():
    """
    Generate all weight combinations where:
    - Ticker 1 (LQQ3.L): 50%, 60%, 70%
    - Tickers 2 & 3: All 10% increment combinations that sum to remaining weight
    """
    combinations = []
    ticker1_weights = [0.50, 0.60, 0.70]
    
    for w1 in ticker1_weights:
        remaining = 1.0 - w1  # Weight left for tickers 2 and 3
        
        # Generate all 10% increment combinations for tickers 2 and 3
        steps = int(remaining / 0.10)  # Number of 10% steps in remaining weight
        
        for i in range(steps + 1):
            w2 = i * 0.10
            w3 = remaining - w2
            
            # Only include if w3 is non-negative and is a multiple of 0.10
            if w3 >= 0 and abs(w3 - round(w3 / 0.10) * 0.10) < 0.001:
                w3 = round(w3 / 0.10) * 0.10  # Round to nearest 0.10
                if w3 >= 0:  # Final check
                    combinations.append((round(w1, 2), round(w2, 2), round(w3, 2)))
    
    return combinations

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
    print("LSE Portfolio Optimizer - 3-Stock with Variable Weights")
    print("=" * 80)
    print(f"Core ticker: {CORE_TICKER} (Variable weights: 50%, 60%, 70%)")
    print(f"Fixed Hedge Ticker: {FIXED_HEDGE_TICKER}")
    print(f"Goal: Find best 3rd ticker and optimal allocation to minimize Max Drawdown")
    print(f"Data source: Cached data from '{DATA_FOLDER}/'")
    print(f"Fixed start date: {START_DATE} (10 years of data)")
    print(f"Minimum trading days required: {MIN_TRADING_DAYS}")
    
    # Load cached data
    print("\nLoading cached ticker data...")
    price_data, ticker_info = load_cached_data()
    
    if not price_data or not ticker_info:
        print("Could not load data. Exiting.")
        return
    
    # Check if core and fixed tickers are available
    if CORE_TICKER not in price_data:
        print(f"ERROR: Core ticker {CORE_TICKER} not found in cached data!")
        return
    if FIXED_HEDGE_TICKER not in price_data:
        print(f"ERROR: Fixed hedge ticker {FIXED_HEDGE_TICKER} not found in cached data!")
        print(f"Please ensure '{FIXED_HEDGE_TICKER.replace('.', '_')}.pkl' exists in '{DATA_FOLDER}' and has enough data.")
        return
    
    print(f"✓ Found {len(price_data)} cached tickers including {CORE_TICKER} and {FIXED_HEDGE_TICKER}")
    
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
    
    # Use curated list of robust ETFs/ETCs as third tickers
    print(f"\nUsing curated list of {len(CURATED_THIRD_TICKERS)} robust ETFs/ETCs as potential third assets...")
    
    # Filter curated list to only include tickers that are available in our cached data
    available_third_tickers = [t for t in CURATED_THIRD_TICKERS if t in price_data and t not in [CORE_TICKER, FIXED_HEDGE_TICKER]]
    
    print(f"✓ Found {len(available_third_tickers)} curated tickers available in cache.")
    print(f"\nWill test combinations with {len(available_third_tickers)} curated tickers as the 3rd asset.")
    
    if len(available_third_tickers) == 0:
        print("ERROR: No curated tickers available in cached data!")
        return
    
    # Test 3-stock portfolios with the fixed hedge
    print(f"\nTesting 3-stock portfolios: {CORE_TICKER} + {FIXED_HEDGE_TICKER} + 1 curated ticker...")
    
    # Generate all weight combinations
    weight_combinations = generate_weight_combinations()
    print(f"Generated {len(weight_combinations)} weight combinations.")
    print("Weight combinations for ticker 1 (LQQ3.L): 50%, 60%, 70%")
    print("Weight combinations for tickers 2 & 3: All 10% increments that sum to remaining weight")
    
    results_3_stock = []
    
    combinations_3 = []
    for third_ticker in available_third_tickers:
        for weights in weight_combinations:
            tickers = [CORE_TICKER, FIXED_HEDGE_TICKER, third_ticker]
            combinations_3.append((tickers, weights, price_data))
    
    total_combinations = len(available_third_tickers) * len(weight_combinations)
    print(f"Will test {total_combinations} total combinations ({len(available_third_tickers)} curated tickers × {len(weight_combinations)} weight combinations) using multi-processing...")
    
    # Process 3-stock combinations in parallel
    batch_size_3 = 50 # Smaller batches for more frequent progress updates
    with ProcessPoolExecutor() as executor:
        futures = []
        for i in range(0, len(combinations_3), batch_size_3):
            batch = combinations_3[i:i+batch_size_3]
            futures.append(executor.submit(test_portfolio_batch, batch))
        
        for i, future in enumerate(as_completed(futures)):
            results_3_stock.extend(future.result())
            if (i + 1) % 10 == 0: # Update progress every 10 batches
                completed = min((i + 1) * batch_size_3, len(combinations_3))
                print(f"Completed {completed}/{len(combinations_3)} combinations")

    print(f"Completed {len(combinations_3)} total combinations, found {len(results_3_stock)} valid portfolios")
    
    # --- Analyze and Save 3-Stock and Final Results ---
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    print("\n" + "=" * 80)
    print("RESULTS ANALYSIS")
    print("=" * 80)
    
    df_3 = pd.DataFrame() # Initialize to ensure it exists for the final summary

    # Best 3-stock portfolios
    if results_3_stock:
        df_3_all = pd.DataFrame(results_3_stock)
        
        # Filter for portfolios with reasonable CAGR (>15%), then sort by highest DPR
        print("\nFiltering 3-stock portfolios for CAGR >= 15% and sorting by best DPR...")
        df_3 = df_3_all[df_3_all['cagr'] >= 0.15].sort_values('dpr', ascending=False)

        if df_3.empty:
            print("No 3-stock portfolios found meeting the criteria (CAGR >= 15%).")
        else:
            print(f"\nTOP 10 THREE-STOCK PORTFOLIOS (CAGR >= 15%, by Highest DPR):")
            print("-" * 120)
            for i, row in df_3.head(10).iterrows():
                portfolio_str = f"{row['tickers'][0]} ({row['weights'][0]:.0%}) + {row['tickers'][1]} ({row['weights'][1]:.0%}) + {row['tickers'][2]} ({row['weights'][2]:.0%})"
                
                # Add asset type info
                other_tickers_list = row['tickers'][1:3]
                asset_types = []
                for ticker in other_tickers_list:
                    if ticker in ticker_info:
                        asset_types.append(ticker_info[ticker]['type'])
                if asset_types:
                    portfolio_str += f" [{', '.join(asset_types)}]"
                
                print(f"{i+1:2d}. {portfolio_str}")
                print(f"    DPR: {row['dpr']:.3f} | CAGR: {row['cagr']:.1%} | MaxDD: {row['max_drawdown']:.1%} | Calmar: {row['calmar']:.3f} | Sharpe: {row['sharpe']:.2f}")
            
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
            
            # Reorder columns for better readability
            cols_ordered = [
                'ticker_1', 'weight_1', 'ticker_2', 'weight_2', 'ticker_3', 'weight_3',
                'asset_type_2', 'asset_type_3', 'total_return', 'cagr', 'volatility', 
                'sharpe', 'sortino', 'dpr', 'max_drawdown', 'calmar'
            ]
            df_3_save = df_3_save[cols_ordered]
            
            filename_3 = f"lse_3stock_variable_weights_results_{timestamp}.csv"
            df_3_save.to_csv(filename_3, index=False)
            print(f"\n✓ 3-stock results saved to {filename_3}")
    
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
        print(f"DPR: {lqq3_metrics['dpr']:.3f}")
        print(f"Volatility: {lqq3_metrics['volatility']:.1%}")
    
    # Final summary
    print(f"\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Determine best drawdown from available, valid results
    best_3_drawdown = df_3.iloc[0]['max_drawdown'] if not df_3.empty else float('inf')
    lqq3_drawdown = lqq3_metrics['max_drawdown'] if lqq3_metrics else float('inf')

    print(f"LQQ3 standalone Max Drawdown: {lqq3_drawdown:.1%}" if lqq3_drawdown != float('inf') else "LQQ3 standalone: N/A")
    print(f"Best 3-stock (CAGR>=15%) Max Drawdown: {best_3_drawdown:.1%}" if best_3_drawdown != float('inf') else "Best 3-stock (CAGR>=15%): None found")

    if best_3_drawdown < lqq3_drawdown:
        improvement = (lqq3_drawdown - best_3_drawdown) / lqq3_drawdown * 100 if lqq3_drawdown > 0 else 0
        print(f"\nRecommendation: The best 3-stock portfolio reduces max drawdown by {improvement:.1f}% vs LQQ3 alone (while maintaining CAGR >= 15%).")
    elif lqq3_drawdown != float('inf'):
        print(f"\nRecommendation: Stick with LQQ3 standalone - no diversified portfolio met the criteria and improved drawdown.")
    
    print(f"\nAnalysis complete! Tested {len(price_data)} valid tickers from LSE.")

def test_problematic_case():
    """Test case for the problematic scenario with limited data."""
    problematic_tickers = ["LQQ3.L", "SGLN.L", "GLEN.L"]  # Example tickers, adjust as needed
    weights = [0.5, 0.5, 0.0]  # Example weights, adjust as needed
    
    # Load limited data for testing
    price_data, ticker_info = load_cached_data()
    
    if not price_data or not ticker_info:
        print("Could not load data for testing. Exiting.")
        return
    
    # Filter price data to only include the problematic tickers
    price_data_filtered = {ticker: price_data[ticker] for ticker in problematic_tickers if ticker in price_data}
    
    if len(price_data_filtered) != len(problematic_tickers):
        print("Warning: Some tickers in the problematic case are not available in the cached data.")
    
    # Backtest the portfolio with the problematic tickers
    metrics = backtest_portfolio(problematic_tickers, weights, price_data_filtered)
    
    if metrics:
        print("Problematic case metrics:")
        print(metrics)
    else:
        print("No valid metrics calculated for the problematic case.")

def test_specific_problematic_case():
    """Test the exact case from the output that showed 146.8% CAGR."""
    price_data, ticker_info = load_cached_data()
    if price_data:
        tickers = ["LQQ3.L", "SGLN.L", "UB01.L"]
        weights = [0.65, 0.20, 0.15]
        print("\n" + "="*80)
        print("TESTING EXACT PROBLEMATIC CASE:")
        print("LQQ3.L (65%) + SGLN.L (20%) + UB01.L (15%)")
        print("Expected: MaxDD: 60.8% | CAGR: 146.8% | Calmar: 2.415")
        print("="*80)
        
        # First run the debug version to see data quality
        debug_backtest_portfolio(tickers, weights, price_data)
        
        # Then run the normal version to see calculated metrics
        print("\n" + "-"*50)
        print("RUNNING NORMAL BACKTEST:")
        print("-"*50)
        metrics = backtest_portfolio(tickers, weights, price_data)
        if metrics:
            print(f"Calculated CAGR: {metrics['cagr']:.1%}")
            print(f"Calculated MaxDD: {metrics['max_drawdown']:.1%}")
            print(f"Calculated Calmar: {metrics['calmar']:.3f}")
            print(f"Total Return: {metrics['total_return']:.1%}")
            print(f"Volatility: {metrics['volatility']:.1%}")
            print(f"Sharpe: {metrics['sharpe']:.2f}")
        else:
            print("No metrics calculated - portfolio was filtered out")

def test_data_quality_only():
    """Just test data quality filtering without running the full analysis."""
    print("Testing data quality filtering...")
    
    price_data, ticker_info = load_cached_data()
    
    if price_data:
        print(f"Final loaded tickers: {len(price_data)}")
        
        # Test the specific problematic ticker
        if "UB01.L" in price_data:
            print("WARNING: UB01.L passed data quality checks - this should not happen!")
            # Let's check its data manually
            data = price_data["UB01.L"]
            returns = data['Close'].pct_change().dropna()
            print(f"UB01.L max return: {returns.max():.4f}")
            print(f"UB01.L min return: {returns.min():.4f}")
        else:
            print("✓ UB01.L was correctly filtered out due to data quality issues")
    
    return price_data, ticker_info

if __name__ == "__main__":
    # Run the main analysis with improved CAGR filtering
    main()
