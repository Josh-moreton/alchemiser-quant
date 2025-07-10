#!/usr/bin/env python3
"""
LSE Portfolio Optimizer - Quick Version
Tests curated list of high-quality LSE tickers for optimal 2-3 stock portfolios with LQQ3.
Optimizes for Calmar ratio with faster execution.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import itertools
import warnings
warnings.filterwarnings('ignore')

# --- Configuration ---
CORE_TICKER = "LQQ3.L"
CORE_WEIGHT = 0.66  # 66% allocation to LQQ3
START_DATE = "2017-01-01"  # More recent period for faster execution
INITIAL_CAPITAL = 100000
MIN_TRADING_DAYS = 252  # Minimum 1 year of data
REBALANCE_FREQUENCY = 'M'  # Monthly rebalancing

# --- Curated High-Quality LSE Tickers ---
# Focus on liquid, well-established stocks and ETFs
CURATED_LSE_TICKERS = [
    # Major UK Stocks
    "SHEL.L", "AZN.L", "ULVR.L", "BP.L", "GSK.L", "DGE.L", "VOD.L", 
    "LLOY.L", "BARC.L", "RR.L", "RIO.L", "BHP.L", "HSBA.L", "NWG.L",
    "GLEN.L", "PRU.L", "LSEG.L", "BT-A.L", "CRH.L", "EXPN.L", "FRES.L",
    "STAN.L", "SSE.L", "TSCO.L", "NXT.L", "IHG.L", "UU.L", "WPP.L",
    "BNZL.L", "DCC.L", "LGEN.L", "OCDO.L", "AUTO.L", "SAGE.L",
    
    # Popular ETFs
    "VUSA.L", "VMID.L", "VEVE.L", "VFEM.L", "VJPN.L", "VEUR.L",
    "ISF.L", "IUSA.L", "IUKD.L", "IDEM.L", "IEVL.L", "IGOV.L",
    
    # 3x Leveraged ETFs
    "TQQQ.L", "QQQ3.L", "3USL.L", "3USS.L",
    
    # REITs
    "LAND.L", "SGRO.L", "BLND.L",
    
    # Defensive/Utilities
    "NG.L", "SVT.L", "CNE.L"
]

def download_data(ticker):
    """Download and clean data for a ticker."""
    try:
        data = yf.download(ticker, start=START_DATE, progress=False)
        if data.empty or len(data) < MIN_TRADING_DAYS:
            return None
        
        if data.columns.nlevels > 1:
            data.columns = data.columns.get_level_values(0)
        
        if 'Close' not in data.columns:
            return None
            
        return data[['Close']].dropna()
    except:
        return None

def calculate_metrics(returns):
    """Calculate portfolio performance metrics."""
    if len(returns) == 0 or returns.std() == 0:
        return None
    
    total_return = (1 + returns).prod() - 1
    years = len(returns) / 252
    cagr = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
    
    volatility = returns.std() * np.sqrt(252)
    sharpe = returns.mean() / returns.std() * np.sqrt(252)
    
    # Sortino
    downside = returns[returns < 0]
    sortino = returns.mean() / downside.std() * np.sqrt(252) if len(downside) > 0 and downside.std() > 0 else 0
    
    # Max Drawdown
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.expanding().max()
    drawdowns = (cumulative - rolling_max) / rolling_max
    max_drawdown = abs(drawdowns.min())
    
    # Calmar Ratio
    calmar = cagr / max_drawdown if max_drawdown > 0 else 0
    
    return {
        'cagr': cagr,
        'volatility': volatility,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'calmar': calmar,
        'total_return': total_return
    }

def backtest_portfolio(tickers, weights, price_data):
    """Backtest portfolio with monthly rebalancing."""
    # Get common dates
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
    
    # Monthly rebalancing
    portfolio_value = 1.0
    portfolio_returns = []
    
    for month_end in returns_df.resample('M').last().index:
        month_returns = returns_df[returns_df.index <= month_end]
        if len(portfolio_returns) > 0:
            # Get returns since last rebalance
            last_month = returns_df.resample('M').last().index[len(portfolio_returns)-1]
            month_returns = returns_df[(returns_df.index > last_month) & (returns_df.index <= month_end)]
        
        if len(month_returns) > 0:
            # Calculate weighted returns for this period
            period_returns = (month_returns * weights).sum(axis=1)
            portfolio_returns.extend(period_returns.tolist())
    
    if len(portfolio_returns) == 0:
        return None
        
    return calculate_metrics(pd.Series(portfolio_returns))

def main():
    print("LSE Portfolio Optimizer - Quick Analysis")
    print("=" * 60)
    print(f"Core: {CORE_TICKER} ({CORE_WEIGHT:.0%})")
    print(f"Period: {START_DATE} to present")
    print(f"Testing {len(CURATED_LSE_TICKERS)} curated LSE tickers")
    
    # Download data
    print("\nDownloading data...")
    price_data = {}
    
    # Always include core ticker
    all_tickers = [CORE_TICKER] + [t for t in CURATED_LSE_TICKERS if t != CORE_TICKER]
    
    for ticker in all_tickers:
        data = download_data(ticker)
        if data is not None:
            price_data[ticker] = data
            print(f"✓ {ticker}")
        else:
            print(f"✗ {ticker}")
    
    if CORE_TICKER not in price_data:
        print(f"ERROR: {CORE_TICKER} not available!")
        return
    
    other_tickers = [t for t in price_data.keys() if t != CORE_TICKER]
    print(f"\nTesting with {len(other_tickers)} other tickers")
    
    # Test 2-stock portfolios
    print("\nTesting 2-stock portfolios...")
    results_2 = []
    
    for other in other_tickers:
        tickers = [CORE_TICKER, other]
        weights = [CORE_WEIGHT, 1 - CORE_WEIGHT]
        metrics = backtest_portfolio(tickers, weights, price_data)
        
        if metrics:
            results_2.append({
                'tickers': tickers,
                'weights': weights,
                **metrics
            })
    
    # Test 3-stock portfolios
    print(f"Testing 3-stock portfolios...")
    results_3 = []
    other_weight = (1 - CORE_WEIGHT) / 2
    
    count = 0
    total_combinations = len(other_tickers) * (len(other_tickers) - 1) // 2
    
    for i, ticker1 in enumerate(other_tickers):
        for ticker2 in other_tickers[i+1:]:
            tickers = [CORE_TICKER, ticker1, ticker2]
            weights = [CORE_WEIGHT, other_weight, other_weight]
            metrics = backtest_portfolio(tickers, weights, price_data)
            
            if metrics:
                results_3.append({
                    'tickers': tickers,
                    'weights': weights,
                    **metrics
                })
            
            count += 1
            if count % 50 == 0:
                print(f"Progress: {count}/{total_combinations}")
    
    # Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    # Best 2-stock portfolios
    if results_2:
        df_2 = pd.DataFrame(results_2).sort_values('calmar', ascending=False)
        print(f"\nTOP 5 TWO-STOCK PORTFOLIOS:")
        print("-" * 50)
        
        for i, row in df_2.head(5).iterrows():
            portfolio = f"{row['tickers'][0]} ({row['weights'][0]:.0%}) + {row['tickers'][1]} ({row['weights'][1]:.0%})"
            print(f"{i+1}. {portfolio}")
            print(f"   Calmar: {row['calmar']:.3f} | CAGR: {row['cagr']:.1%} | MaxDD: {row['max_drawdown']:.1%}")
    
    # Best 3-stock portfolios
    if results_3:
        df_3 = pd.DataFrame(results_3).sort_values('calmar', ascending=False)
        print(f"\nTOP 5 THREE-STOCK PORTFOLIOS:")
        print("-" * 70)
        
        for i, row in df_3.head(5).iterrows():
            portfolio = f"{row['tickers'][0]} ({row['weights'][0]:.0%}) + {row['tickers'][1]} ({row['weights'][1]:.0%}) + {row['tickers'][2]} ({row['weights'][2]:.0%})"
            print(f"{i+1}. {portfolio}")
            print(f"   Calmar: {row['calmar']:.3f} | CAGR: {row['cagr']:.1%} | MaxDD: {row['max_drawdown']:.1%}")
    
    # LQQ3 standalone
    print(f"\nLQQ3 STANDALONE:")
    lqq3_metrics = backtest_portfolio([CORE_TICKER], [1.0], price_data)
    if lqq3_metrics:
        print(f"Calmar: {lqq3_metrics['calmar']:.3f} | CAGR: {lqq3_metrics['cagr']:.1%} | MaxDD: {lqq3_metrics['max_drawdown']:.1%}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if results_2:
        df_2_save = df_2.copy()
        df_2_save['ticker_1'] = df_2_save['tickers'].str[0]
        df_2_save['ticker_2'] = df_2_save['tickers'].str[1]
        df_2_save['weight_1'] = df_2_save['weights'].str[0]
        df_2_save['weight_2'] = df_2_save['weights'].str[1]
        df_2_save = df_2_save.drop(['tickers', 'weights'], axis=1)
        df_2_save.to_csv(f"lse_2stock_quick_results_{timestamp}.csv", index=False)
        print(f"\n2-stock results saved to lse_2stock_quick_results_{timestamp}.csv")
    
    if results_3:
        df_3_save = df_3.copy()
        df_3_save['ticker_1'] = df_3_save['tickers'].str[0]
        df_3_save['ticker_2'] = df_3_save['tickers'].str[1]
        df_3_save['ticker_3'] = df_3_save['tickers'].str[2]
        df_3_save['weight_1'] = df_3_save['weights'].str[0]
        df_3_save['weight_2'] = df_3_save['weights'].str[1]
        df_3_save['weight_3'] = df_3_save['weights'].str[2]
        df_3_save = df_3_save.drop(['tickers', 'weights'], axis=1)
        df_3_save.to_csv(f"lse_3stock_quick_results_{timestamp}.csv", index=False)
        print(f"3-stock results saved to lse_3stock_quick_results_{timestamp}.csv")
    
    print(f"\nAnalysis complete!")
    if results_2 and results_3:
        best_2_calmar = df_2.iloc[0]['calmar']
        best_3_calmar = df_3.iloc[0]['calmar']
        winner = "3-stock" if best_3_calmar > best_2_calmar else "2-stock"
        print(f"Best portfolio: {winner} with Calmar ratio of {max(best_2_calmar, best_3_calmar):.3f}")

if __name__ == "__main__":
    main()
