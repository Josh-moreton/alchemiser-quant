#!/usr/bin/env python3
"""
Grid Search for 200-day SMA Variations on LQQ3 Strategy
- Laddered entry/exit
- SMA buffer (entry/exit threshold)
- Signal source: TQQQ, QQQ, or both
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import itertools

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

def run_backtest(lqq3, entry_signal, exit_signal, ladder_steps):
    # ladder_steps: e.g. [0.33, 0.66, 1.0]
    portfolio = []
    cash = 10000
    shares = 0
    allocation = 0
    for date, row in lqq3.iterrows():
        price = row['Close']
        # Determine target allocation
        if row[entry_signal] and not row[exit_signal]:
            # Ladder in
            if allocation < 1.0:
                allocation = min(1.0, allocation + ladder_steps)
        elif row[exit_signal]:
            # Ladder out
            if allocation > 0:
                allocation = max(0, allocation - ladder_steps)
        # Rebalance
        target_value = cash + shares * price
        target_shares = (target_value * allocation) / price
        shares = target_shares
        cash = target_value - shares * price
        portfolio.append({'Date': date, 'Cash': cash, 'Shares': shares, 'Portfolio': cash + shares * price, 'Allocation': allocation})
    return pd.DataFrame(portfolio).set_index('Date')

def grid_search(
    sma_windows=[200],
    buffer_pcts=[0, 2],
    ladder_steps=[0.33, 0.5, 1.0],
    entry_tickers=['TQQQ', 'QQQ'],
    exit_tickers=['TQQQ', 'QQQ'],
    start_date="2012-01-01",
    end_date=None
):
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    tickers = set(entry_tickers + exit_tickers + ['LQQ3.L'])
    data = fetch_data(tickers, start_date, end_date)
    lqq3 = data['LQQ3.L']
    results = []
    for sma_win, buf, entry_tkr, exit_tkr, step in itertools.product(
        sma_windows, buffer_pcts, entry_tickers, exit_tickers, ladder_steps
    ):
        entry_df = generate_signals(data[entry_tkr], sma_win, buf)
        exit_df = generate_signals(data[exit_tkr], sma_win, buf)
        # Align dates
        lqq3_aligned = lqq3.copy()
        lqq3_aligned['Entry'] = entry_df['Above_SMA'].reindex(lqq3.index).fillna(0)
        lqq3_aligned['Exit'] = exit_df['Below_SMA'].reindex(lqq3.index).fillna(0)
        # Run backtest
        pf = run_backtest(lqq3_aligned, 'Entry', 'Exit', step)
        total_return = pf['Portfolio'].iloc[-1] / pf['Portfolio'].iloc[0] - 1
        max_dd = (pf['Portfolio'] / pf['Portfolio'].cummax() - 1).min()
        results.append({
            'SMA': sma_win,
            'Buffer%': buf,
            'Ladder Step': step,
            'Entry Ticker': entry_tkr,
            'Exit Ticker': exit_tkr,
            'Total Return %': round(total_return*100, 2),
            'Max Drawdown %': round(max_dd*100, 2)
        })
    return pd.DataFrame(results)

if __name__ == "__main__":
    df = grid_search(
        sma_windows=[180, 200, 220],
        buffer_pcts=[0, 1, 2],
        ladder_steps=[0.33, 0.5, 1.0],
        entry_tickers=['TQQQ', 'QQQ'],
        exit_tickers=['TQQQ', 'QQQ'],
        start_date="2015-01-01"
    )
    print(df.sort_values('Total Return %', ascending=False).head(20))
    df.to_csv("sma_variation_grid_search_results.csv", index=False)