#!/usr/bin/env python3
"""
Compare QQQ vs TQQQ as 200-day SMA signal for LQQ3 laddered strategy
Outputs all key performance metrics for both signal sources
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

def fetch_data(tickers, start_date, end_date):
    data = {}
    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.columns.nlevels > 1:
            df.columns = df.columns.get_level_values(0)
        data[ticker] = df
    return data

def generate_signals(df, sma_window, buffer_pct):
    df = df.copy()
    df['SMA'] = df['Close'].rolling(window=sma_window).mean()
    df['Above_SMA'] = (df['Close'] > df['SMA'] * (1 + buffer_pct/100)).astype(int)
    df['Below_SMA'] = (df['Close'] < df['SMA'] * (1 - buffer_pct/100)).astype(int)
    return df

def run_backtest(lqq3, entry_signal, exit_signal, ladder_step):
    portfolio = []
    cash = 55000
    shares = 0
    allocation = 0
    for date, row in lqq3.iterrows():
        price = row['Close']
        # Determine target allocation
        if row[entry_signal] and not row[exit_signal]:
            if allocation < 1.0:
                allocation = min(1.0, allocation + ladder_step)
        elif row[exit_signal]:
            if allocation > 0:
                allocation = max(0, allocation - ladder_step)
        # Rebalance
        target_value = cash + shares * price
        target_shares = (target_value * allocation) / price
        shares = target_shares
        cash = target_value - shares * price
        portfolio.append({'Date': date, 'Cash': cash, 'Shares': shares, 'Portfolio': cash + shares * price, 'Allocation': allocation})
    return pd.DataFrame(portfolio).set_index('Date')

def calculate_metrics(pf):
    pf = pf.copy()
    pf['Daily_Return'] = pf['Portfolio'].pct_change()
    pf['Cumulative_Return'] = pf['Portfolio'] / pf['Portfolio'].iloc[0] - 1
    total_return = pf['Portfolio'].iloc[-1] / pf['Portfolio'].iloc[0] - 1
    max_dd = (pf['Portfolio'] / pf['Portfolio'].cummax() - 1).min()
    volatility = pf['Daily_Return'].std() * np.sqrt(252)
    sharpe = pf['Daily_Return'].mean() / pf['Daily_Return'].std() * np.sqrt(252) if pf['Daily_Return'].std() > 0 else 0
    win_rate = (pf['Daily_Return'] > 0).sum() / pf['Daily_Return'].count()
    return {
        'Total Return %': round(total_return*100, 2),
        'Max Drawdown %': round(max_dd*100, 2),
        'Volatility %': round(volatility*100, 2),
        'Sharpe Ratio': round(sharpe, 3),
        'Win Rate %': round(win_rate*100, 2),
        'Final Value': round(pf['Portfolio'].iloc[-1], 2)
    }

def compare_signals(start_date="2011-01-01", end_date=None, sma_window=200, buffer_pct=0, ladder_step=0.33):
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    tickers = ['LQQ3.L', 'QQQ', 'TQQQ']
    data = fetch_data(tickers, start_date, end_date)
    lqq3 = data['LQQ3.L']
    results = {}
    for signal_ticker in ['QQQ', 'TQQQ']:
        sig_df = generate_signals(data[signal_ticker], sma_window, buffer_pct)
        lqq3_aligned = lqq3.copy()
        lqq3_aligned['Entry'] = sig_df['Above_SMA'].reindex(lqq3.index).fillna(0)
        lqq3_aligned['Exit'] = sig_df['Below_SMA'].reindex(lqq3.index).fillna(0)
        pf = run_backtest(lqq3_aligned, 'Entry', 'Exit', ladder_step)
        metrics = calculate_metrics(pf)
        results[signal_ticker] = metrics
    return results

def print_comparison_table(results):
    print("\nQQQ vs TQQQ 200-day SMA Signal Comparison (Laddered, 0% buffer)")
    print("="*60)
    print(f"{'Signal':<8} | {'TotalRet%':>8} | {'MaxDD%':>8} | {'Vol%':>8} | {'Sharpe':>7} | {'WinRate%':>9} | {'FinalValue':>10}")
    print("-"*60)
    for sig, m in results.items():
        print(f"{sig:<8} | {m['Total Return %']:>8.2f} | {m['Max Drawdown %']:>8.2f} | {m['Volatility %']:>8.2f} | {m['Sharpe Ratio']:>7.3f} | {m['Win Rate %']:>9.2f} | {m['Final Value']:>10.2f}")
    print("="*60)

if __name__ == "__main__":
    results = compare_signals(
        start_date="2015-01-01",
        sma_window=200,
        buffer_pct=0,
        ladder_step=0.33
    )
    print_comparison_table(results)
