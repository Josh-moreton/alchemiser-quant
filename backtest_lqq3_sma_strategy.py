#!/usr/bin/env python3
"""
Backtest for LQQ3 150-day SMA Strategy (100% in/out)
Generates detailed stats, trade log, and plots.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import itertools

# --- Config ---
SIGNAL_TICKER = "TQQQ"
TRADE_TICKER = "LQQ3.L"
SMA_PERIOD = 200
START_DATE = "2010-01-01"  # or earliest available
INITIAL_CAPITAL = 100000
COMMISSION = 0.001  # 0.1% per trade

# --- Download Data ---
signal_data = yf.download(SIGNAL_TICKER, start=START_DATE)
trade_data = yf.download(TRADE_TICKER, start=START_DATE)
if signal_data.empty or trade_data.empty:
    raise ValueError(f"No data for {SIGNAL_TICKER} or {TRADE_TICKER}")
if signal_data.columns.nlevels > 1:
    signal_data.columns = signal_data.columns.get_level_values(0)
if trade_data.columns.nlevels > 1:
    trade_data.columns = trade_data.columns.get_level_values(0)
if 'Close' not in signal_data.columns or 'Open' not in trade_data.columns:
    raise ValueError("No 'Close' in signal or 'Open' in trade data")
signal_data['SMA'] = signal_data['Close'].rolling(window=SMA_PERIOD).mean()
signal_data = signal_data.dropna(subset=['SMA'])

# --- Align Dates (signal on T, trade on T+1 open) ---
signal_df = signal_data[['Close', 'SMA']].copy()
signal_df['Signal'] = (signal_df['Close'] > signal_df['SMA']).astype(int)
signal_df['Signal_Change'] = signal_df['Signal'].diff().fillna(0)
signal_df = signal_df[['Signal', 'Signal_Change']]

# Shift signal changes forward by 1 day to trade on next open
signal_df_shifted = signal_df.shift(1)

# Align with trade_data (UK market)
combined = pd.DataFrame(index=trade_data.index)
combined['Trade_Open'] = trade_data['Open']
combined['Signal'] = signal_df_shifted['Signal']
combined['Signal_Change'] = signal_df_shifted['Signal_Change']
combined = combined.dropna(subset=['Signal'])

# --- Backtest Logic ---
trades = []
position = 0
entry_date = None
entry_price = None
capital = INITIAL_CAPITAL
cash = INITIAL_CAPITAL
shares = 0
peak = INITIAL_CAPITAL
max_dd = 0

equity_curve = []
drawdowns = []
trade_returns = []
trade_durations = []
trade_wins = []

for i, row in combined.iterrows():
    date = i
    price = row['Trade_Open']
    signal = row['Signal']
    signal_change = row['Signal_Change']
    # Entry
    if position == 0 and signal_change == 1:
        shares = cash // price
        entry_price = price
        entry_date = date
        cost = shares * price * (1 + COMMISSION)
        cash -= cost
        position = 1
    # Exit
    elif position == 1 and signal_change == -1:
        proceeds = shares * price * (1 - COMMISSION)
        cash += proceeds
        ret = (price - entry_price) / entry_price
        duration = (date - entry_date).days
        trades.append({
            'Entry Date': entry_date,
            'Exit Date': date,
            'Entry Price': entry_price,
            'Exit Price': price,
            'Return': ret,
            'Duration': duration
        })
        trade_returns.append(ret)
        trade_durations.append(duration)
        trade_wins.append(ret > 0)
        shares = 0
        entry_price = None
        entry_date = None
        position = 0
    # Update equity
    equity = cash + (shares * price if position else 0)
    equity_curve.append(equity)
    peak = max(peak, equity)
    dd = (peak - equity) / peak
    drawdowns.append(dd)
    max_dd = max(max_dd, dd)

# If still in position at end, close it
if position == 1:
    price = combined.iloc[-1]['Trade_Open']
    date = combined.index[-1]
    proceeds = shares * price * (1 - COMMISSION)
    cash += proceeds
    ret = (price - entry_price) / entry_price
    duration = (date - entry_date).days
    trades.append({
        'Entry Date': entry_date,
        'Exit Date': date,
        'Entry Price': entry_price,
        'Exit Price': price,
        'Return': ret,
        'Duration': duration
    })
    trade_returns.append(ret)
    trade_durations.append(duration)
    trade_wins.append(ret > 0)
    shares = 0
    entry_price = None
    entry_date = None
    position = 0

final_equity = cash

equity_curve = np.array(equity_curve)
drawdowns = np.array(drawdowns)

# --- Stats ---
trades_df = pd.DataFrame(trades)
trades_per_year = len(trades_df) / ((combined.index[-1] - combined.index[0]).days / 365.25)
win_rate = trades_df['Return'].gt(0).mean() if not trades_df.empty else 0
avg_win = trades_df[trades_df['Return'] > 0]['Return'].mean() if not trades_df.empty else 0
avg_loss = trades_df[trades_df['Return'] <= 0]['Return'].mean() if not trades_df.empty else 0
profit_factor = -avg_win / avg_loss if avg_loss != 0 else np.nan
expectancy = trades_df['Return'].mean() if not trades_df.empty else 0
best_trade = trades_df['Return'].max() if not trades_df.empty else 0
worst_trade = trades_df['Return'].min() if not trades_df.empty else 0
longest_win_streak = (trades_df['Return'] > 0).astype(int).groupby((trades_df['Return'] <= 0).astype(int).cumsum()).cumsum().max() if not trades_df.empty else 0
longest_loss_streak = (trades_df['Return'] <= 0).astype(int).groupby((trades_df['Return'] > 0).astype(int).cumsum()).cumsum().max() if not trades_df.empty else 0

# Annualized stats
years = (combined.index[-1] - combined.index[0]).days / 365.25
total_return = (final_equity / INITIAL_CAPITAL) - 1
cagr = (final_equity / INITIAL_CAPITAL) ** (1/years) - 1
returns = pd.Series(equity_curve).pct_change().dropna()
volatility = returns.std() * np.sqrt(252)
sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else np.nan
sortino = returns.mean() / returns[returns < 0].std() * np.sqrt(252) if returns[returns < 0].std() > 0 else np.nan
max_drawdown = max_dd

# Buy & hold
bh_start = combined.iloc[0]['Trade_Open']
bh_end = combined.iloc[-1]['Trade_Open']
bh_return = (bh_end / bh_start) - 1
bh_cagr = (bh_end / bh_start) ** (1/years) - 1

# --- Output ---
print("\n===== LQQ3 150-day SMA Strategy Backtest (TQQQ Signal, Trade on Next Open) =====")
print(f"Period: {combined.index[0].date()} to {combined.index[-1].date()} ({years:.2f} years)")
print(f"Initial capital: ${INITIAL_CAPITAL:,.2f}")
print(f"Final equity:   ${final_equity:,.2f}")
print(f"Total return:   {total_return*100:.2f}%")
print(f"CAGR:           {cagr*100:.2f}%")
print(f"Max drawdown:   {max_drawdown*100:.2f}%")
print(f"Sharpe ratio:   {sharpe:.2f}")
print(f"Sortino ratio:  {sortino:.2f}")
print(f"Volatility:     {volatility*100:.2f}%")
print(f"Number of trades: {len(trades_df)}")
print(f"Trades/year:      {trades_per_year:.2f}")
print(f"Win rate:         {win_rate*100:.2f}%")
print(f"Avg win:          {avg_win*100:.2f}%")
print(f"Avg loss:         {avg_loss*100:.2f}%")
print(f"Profit factor:    {profit_factor:.2f}")
print(f"Expectancy:       {expectancy*100:.2f}%")
print(f"Best trade:       {best_trade*100:.2f}%")
print(f"Worst trade:      {worst_trade*100:.2f}%")
print(f"Longest win streak:  {longest_win_streak}")
print(f"Longest loss streak: {longest_loss_streak}")
print("\nBuy & Hold LQQ3:")
print(f"  Total return: {bh_return*100:.2f}%  CAGR: {bh_cagr*100:.2f}%")

# --- Save trade log ---
trades_df.to_csv("lqq3_sma_trades.csv", index=False)
print("Trade log saved to lqq3_sma_trades.csv")

# --- Annual returns ---
annual = pd.DataFrame({'Equity': equity_curve}, index=combined.index).resample('Y').last()
annual['Return'] = annual['Equity'].pct_change()
print("\nAnnual Returns:")
print(annual['Return'].dropna().apply(lambda x: f"{x*100:.2f}%"))

# --- Buffer grid search ---
# Buffer values from -3.0% to +3.0% in 0.5% steps (inclusive)
buffer_values = np.arange(-3.0, 3.01, 0.5)
# Note: Negative buffer values lower the entry threshold (easier to enter, harder to exit)
results = []

for entry_buffer, exit_buffer in itertools.product(buffer_values, buffer_values):
    # --- Signal logic with buffer (match main backtest logic) ---
    signal_df = signal_data[['Close', 'SMA']].copy()
    # Entry: Close > SMA * (1 + entry_buffer/100), Exit: Close < SMA * (1 - exit_buffer/100)
    signal_df['Signal'] = 0
    signal_df.loc[signal_df['Close'] > signal_df['SMA'] * (1 + entry_buffer/100), 'Signal'] = 1
    signal_df.loc[signal_df['Close'] < signal_df['SMA'] * (1 - exit_buffer/100), 'Signal'] = 0
    signal_df['Signal_Change'] = signal_df['Signal'].diff().fillna(0)
    signal_df = signal_df[['Signal', 'Signal_Change']]
    # Print debug info for first buffer combo
    if entry_buffer == 0.0 and exit_buffer == 0.0:
        print("\n[DEBUG] Buffer=0.0, DataFrame head:")
        print(signal_df.head(10))
        print(f"Any Signal==1? {signal_df['Signal'].eq(1).any()}")
        print(f"Any Signal==0? {signal_df['Signal'].eq(0).any()}")
        print(f"Signal_Change==1: {signal_df['Signal_Change'].eq(1).sum()} | Signal_Change==-1: {signal_df['Signal_Change'].eq(-1).sum()}")
    # Shift for next day trade
    signal_df_shifted = signal_df.shift(1)
    # --- Align with trade_data (UK market) using intersection of available dates ---
    valid_idx = trade_data.index.intersection(signal_df_shifted.index)
    combined = pd.DataFrame(index=valid_idx)
    combined['Trade_Open'] = trade_data.loc[valid_idx, 'Open']
    combined['Signal'] = signal_df_shifted.loc[valid_idx, 'Signal']
    combined['Signal_Change'] = signal_df_shifted.loc[valid_idx, 'Signal_Change']
    combined = combined.dropna(subset=['Signal'])

    # Debug: print number of entry/exit signals and combined rows
    num_entry_signals = signal_df['Signal_Change'].eq(1).sum()
    num_exit_signals = signal_df['Signal_Change'].eq(-1).sum()
    print(f"Buffer Entry={entry_buffer:.1f}%, Exit={exit_buffer:.1f}%: Entry signals={num_entry_signals}, Exit signals={num_exit_signals}, Combined rows={len(combined)}")

    # --- Backtest Logic ---
    trades = []
    position = 0
    entry_date = None
    entry_price = None
    cash = INITIAL_CAPITAL
    shares = 0
    equity_curve = []
    peak = INITIAL_CAPITAL
    max_dd = 0
    returns = []
    for i, row in combined.iterrows():
        date = i
        price = row['Trade_Open']
        signal = row['Signal']
        signal_change = row['Signal_Change']
        if position == 0 and signal_change == 1:
            shares = cash // price
            entry_price = price
            entry_date = date
            cost = shares * price * (1 + COMMISSION)
            cash -= cost
            position = 1
        elif position == 1 and signal_change == -1:
            proceeds = shares * price * (1 - COMMISSION)
            cash += proceeds
            ret = (price - entry_price) / entry_price
            duration = (date - entry_date).days
            trades.append({'Entry Date': entry_date, 'Exit Date': date, 'Entry Price': entry_price, 'Exit Price': price, 'Return': ret, 'Duration': duration})
            shares = 0
            entry_price = None
            entry_date = None
            position = 0
        equity = cash + (shares * price if position else 0)
        equity_curve.append(equity)
        peak = max(peak, equity)
        dd = (peak - equity) / peak
        max_dd = max(max_dd, dd)
        returns.append(equity)
    if position == 1:
        price = combined.iloc[-1]['Trade_Open']
        date = combined.index[-1]
        proceeds = shares * price * (1 - COMMISSION)
        cash += proceeds
        ret = (price - entry_price) / entry_price
        duration = (date - entry_date).days
        trades.append({'Entry Date': entry_date, 'Exit Date': date, 'Entry Price': entry_price, 'Exit Price': price, 'Return': ret, 'Duration': duration})
        shares = 0
        entry_price = None
        entry_date = None
        position = 0
    final_equity = cash
    trades_df = pd.DataFrame(trades)
    years = (combined.index[-1] - combined.index[0]).days / 365.25 if len(combined) > 1 else 0
    total_return = (final_equity / INITIAL_CAPITAL) - 1 if years > 0 else 0
    cagr = (final_equity / INITIAL_CAPITAL) ** (1/years) - 1 if years > 0 else 0
    trades_per_year = len(trades_df) / years if years > 0 else 0
    win_rate = trades_df['Return'].gt(0).mean() if not trades_df.empty else 0
    avg_win = trades_df[trades_df['Return'] > 0]['Return'].mean() if not trades_df.empty else 0
    avg_loss = trades_df[trades_df['Return'] <= 0]['Return'].mean() if not trades_df.empty else 0
    profit_factor = -avg_win / avg_loss if avg_loss != 0 else np.nan
    expectancy = trades_df['Return'].mean() if not trades_df.empty else 0
    best_trade = trades_df['Return'].max() if not trades_df.empty else 0
    worst_trade = trades_df['Return'].min() if not trades_df.empty else 0
    # Drawdown, Sharpe, Sortino
    equity_curve_np = np.array(equity_curve)
    drawdowns = (np.maximum.accumulate(equity_curve_np) - equity_curve_np) / np.maximum.accumulate(equity_curve_np)
    max_drawdown = drawdowns.max() if len(drawdowns) > 0 else 0
    returns_pct = pd.Series(equity_curve_np).pct_change().dropna()
    sharpe = returns_pct.mean() / returns_pct.std() * np.sqrt(252) if returns_pct.std() > 0 else np.nan
    sortino = returns_pct.mean() / returns_pct[returns_pct < 0].std() * np.sqrt(252) if returns_pct[returns_pct < 0].std() > 0 else np.nan
    results.append({
        'Entry_Buffer_%': entry_buffer,
        'Exit_Buffer_%': exit_buffer,
        'Total_Return_%': total_return*100,
        'CAGR_%': cagr*100,
        'Num_Trades': len(trades_df),
        'Trades_per_Year': trades_per_year,
        'Win_Rate_%': win_rate*100,
        'Avg_Win_%': avg_win*100,
        'Avg_Loss_%': avg_loss*100,
        'Profit_Factor': profit_factor,
        'Expectancy_%': expectancy*100,
        'Best_Trade_%': best_trade*100,
        'Worst_Trade_%': worst_trade*100,
        'Final_Equity': final_equity,
        'Max_Drawdown_%': max_drawdown*100,
        'Sharpe': sharpe,
        'Sortino': sortino
    })

# --- Output summary table ---
results_df = pd.DataFrame(results)
print("\n=== SMA Buffer Grid Search Results ===")
print(results_df.sort_values('Total_Return_%', ascending=False).to_string(index=False))
results_df.to_csv("lqq3_sma_buffer_gridsearch.csv", index=False)
print("\nFull results saved to lqq3_sma_buffer_gridsearch.csv")

print("\nAll done!")
