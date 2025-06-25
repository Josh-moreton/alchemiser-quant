import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# --- Data Fetching ---
def fetch_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date, progress=False)
    if data.empty:
        raise ValueError(f"Failed to fetch data for {symbol}.")
    if data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)
    return data

def align_data(signal_df, trade_df):
    # Align on date index, inner join
    df = pd.DataFrame(index=signal_df.index.intersection(trade_df.index))
    df['Signal_Close'] = signal_df.loc[df.index, 'Close']
    df['Trade_Close'] = trade_df.loc[df.index, 'Close']
    return df

# --- Signal Calculations ---
def calc_macd(df, fast=12, slow=26, signal=9):
    ema_fast = df['Close'].ewm(span=fast).mean()
    ema_slow = df['Close'].ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    return macd, macd_signal

def calc_sma(df, period=200):
    return df['Close'].rolling(window=period).mean()

def calc_multi_indicator(df):
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_100'] = df['Close'].rolling(window=100).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    macd, macd_signal = calc_macd(df)
    score = (
        (df['Close'] > df['SMA_50']).astype(int) +
        (df['SMA_50'] > df['SMA_100']).astype(int) +
        (df['SMA_100'] > df['SMA_200']).astype(int) +
        (macd > macd_signal).astype(int)
    )
    return (score >= 3).astype(int)

# --- Backtest Engine ---
def run_backtest(trade_df, signals, initial_capital=55000, allocation=None):
    cash = initial_capital
    shares = 0
    portfolio = []
    for i, (date, row) in enumerate(trade_df.iterrows()):
        price = row['Trade_Close']
        signal = signals.iloc[i]
        alloc = allocation.iloc[i] if allocation is not None else 1.0
        if i == 0:
            portfolio.append({'Date': date, 'Cash': cash, 'Shares': shares, 'Value': cash, 'Signal': signal})
            continue
        prev_signal = signals.iloc[i-1]
        # Entry/exit logic
        if signal > prev_signal:  # Buy
            invest = cash * alloc
            new_shares = invest / price
            shares += new_shares
            cash -= invest
        elif signal < prev_signal:  # Sell
            sell_shares = shares * 0.66
            cash += sell_shares * price
            shares -= sell_shares
        value = cash + shares * price
        portfolio.append({'Date': date, 'Cash': cash, 'Shares': shares, 'Value': value, 'Signal': signal})
    return pd.DataFrame(portfolio).set_index('Date')

# --- Metrics ---
def calc_metrics(portfolio, initial_capital):
    port = portfolio.copy()
    port['Daily_Return'] = port['Value'].pct_change()
    final_value = port['Value'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100
    rolling_max = port['Value'].expanding().max()
    drawdown = (port['Value'] - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    sharpe = port['Daily_Return'].mean() / port['Daily_Return'].std() * np.sqrt(252) if port['Daily_Return'].std() != 0 else 0

    # --- Advanced Metrics ---
    # Number of trades (count signal changes)
    signals = port['Signal']
    signal_changes = signals.diff().fillna(0)
    num_trades = int((signal_changes != 0).sum())
    # Trades per year
    num_years = (port.index[-1] - port.index[0]).days / 365.25
    trades_per_year = num_trades / num_years if num_years > 0 else 0
    # Time in market (% of days with signal > 0)
    time_in_market = (signals > 0).sum() / len(signals) * 100
    # Win rate (profitable trades)
    # Find entry/exit points
    trade_entries = port[(signal_changes > 0)].index
    trade_exits = port[(signal_changes < 0)].index
    # Align entries/exits (ignore open trade at end)
    n = min(len(trade_entries), len(trade_exits))
    trade_entries = trade_entries[:n]
    trade_exits = trade_exits[:n]
    wins = 0
    total = 0
    for entry, exit in zip(trade_entries, trade_exits):
        entry_val = port.loc[entry, 'Value']
        exit_val = port.loc[exit, 'Value']
        if exit_val > entry_val:
            wins += 1
        total += 1
    win_rate = (wins / total * 100) if total > 0 else 0

    return {
        'Total Return (%)': float(round(total_return, 2)),
        'Max Drawdown (%)': float(round(max_drawdown, 2)),
        'Sharpe Ratio': float(round(sharpe, 2)),
        'Final Value': float(round(final_value, 2)),
        'Num Trades': num_trades,
        'Trades/Year': float(round(trades_per_year, 2)),
        'Time in Market (%)': float(round(time_in_market, 2)),
        'Win Rate (%)': float(round(win_rate, 2)),
    }

# --- Strategy Variations ---
def get_signals(df, strategy, params):
    if strategy == 'macd':
        macd, macd_signal = calc_macd(df, **params)
        return (macd > macd_signal).astype(int)
    elif strategy == 'sma':
        sma = calc_sma(df, **params)
        return (df['Close'] > sma).astype(int)
    elif strategy == 'or':
        macd, macd_signal = calc_macd(df)
        sma = calc_sma(df)
        return ((macd > macd_signal) | (df['Close'] > sma)).astype(int)
    elif strategy == 'and':
        macd, macd_signal = calc_macd(df)
        sma = calc_sma(df)
        return ((macd > macd_signal) & (df['Close'] > sma)).astype(int)
    elif strategy == 'weighted':
        macd, macd_signal = calc_macd(df)
        sma = calc_sma(df)
        macd_bull = (macd > macd_signal).astype(int)
        sma_bull = (df['Close'] > sma).astype(int)
        score = macd_bull * params['macd_weight'] + sma_bull * params['sma_weight']
        return (score > params['threshold']).astype(int)
    elif strategy == 'variable':
        macd, macd_signal = calc_macd(df)
        sma = calc_sma(df)
        macd_bull = (macd > macd_signal).astype(int)
        sma_bull = (df['Close'] > sma).astype(int)
        count = macd_bull + sma_bull
        alloc = count.map({0:0.0, 1:0.5, 2:1.0})
        return (count > 0).astype(int), alloc
    elif strategy == 'multi':
        return calc_multi_indicator(df)
    else:
        raise ValueError('Unknown strategy')

# --- Markdown Output Functions ---
def format_result(result, strategy_name, signal_source):
    if result is None:
        return f"### {strategy_name.upper()}\n\n❌ **No results with drawdown better than -50%, ≤12 trades/year, and ≤90% time in market**\n"
    
    md = f"### {strategy_name.upper()}\n\n"
    md += f"✅ **Best Parameters:** {result.get('Params', 'N/A')}\n\n"
    md += f"| Metric | Value |\n"
    md += f"|--------|-------|\n"
    md += f"| **Total Return** | {result['Total Return (%)']:.2f}% |\n"
    md += f"| **Max Drawdown** | {result['Max Drawdown (%)']:.2f}% |\n"
    md += f"| **Sharpe Ratio** | {result['Sharpe Ratio']:.2f} |\n"
    md += f"| **Final Value** | £{result['Final Value']:,.2f} |\n"
    md += f"| **Num Trades** | {result['Num Trades']} |\n"
    md += f"| **Trades/Year** | {result['Trades/Year']:.2f} |\n"
    md += f"| **Time in Market** | {result['Time in Market (%)']:.2f}% |\n"
    md += f"| **Win Rate** | {result['Win Rate (%)']:.2f}% |\n\n"
    return md

def save_markdown_report(all_results, start_date, end_date, initial_capital):
    md = f"# LQQ3 Trading Strategy Optimization Results\n\n"
    md += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    md += f"**Backtest Period:** {start_date} to {end_date}\n\n"
    md += f"**Initial Capital:** £{initial_capital:,}\n\n"
    md += f"**Trading Asset:** LQQ3.L\n\n"
    md += f"**Objective:** Find strategies with drawdown better than -50%, ≤12 trades/year, and ≤90% time in market\n\n"
    md += f"---\n\n"
    
    for signal_source, results in all_results.items():
        md += f"## {signal_source} as Signal Source\n\n"
        
        # Filter valid results and sort by total return
        valid_results = [(k, v) for k, v in results.items() if v is not None]
        valid_results.sort(key=lambda x: x[1]['Total Return (%)'], reverse=True)
        
        if valid_results:
            md += f"### 📊 Performance Summary\n\n"
            md += f"| Strategy | Total Return | Max Drawdown | Sharpe | Trades/Year | Time in Market | Win Rate | Final Value |\n"
            md += f"|----------|--------------|--------------|--------|-------------|----------------|----------|-------------|\n"
            for strategy, result in valid_results:
                md += f"| **{strategy.upper()}** | {result['Total Return (%)']:.1f}% | {result['Max Drawdown (%)']:.1f}% | {result['Sharpe Ratio']:.2f} | {result['Trades/Year']:.2f} | {result['Time in Market (%)']:.1f}% | {result['Win Rate (%)']:.1f}% | £{result['Final Value']:,.0f} |\n"
            md += f"\n"
            
            md += f"### 🏆 Winner: {valid_results[0][0].upper()}\n\n"
            winner = valid_results[0][1]
            md += f"- **Total Return:** {winner['Total Return (%)']:.1f}%\n"
            md += f"- **Max Drawdown:** {winner['Max Drawdown (%)']:.1f}%\n"
            md += f"- **Sharpe Ratio:** {winner['Sharpe Ratio']:.2f}\n"
            md += f"- **Trades/Year:** {winner['Trades/Year']:.2f}\n"
            md += f"- **Time in Market:** {winner['Time in Market (%)']:.1f}%\n"
            md += f"- **Win Rate:** {winner['Win Rate (%)']:.1f}%\n"
            md += f"- **Final Value:** £{winner['Final Value']:,.0f}\n"
            if 'Params' in winner:
                md += f"- **Parameters:** {winner['Params']}\n"
            md += f"\n"
        else:
            md += f"❌ **No strategies met the constraints**\n\n"
        
        md += f"### 📋 Detailed Results\n\n"
        for strategy in ['macd', 'sma', 'or', 'and', 'weighted', 'variable', 'multi']:
            result = results.get(strategy)
            md += format_result(result, strategy, signal_source)
        
        md += f"---\n\n"
    
    # Overall comparison
    all_valid = []
    for signal_source, results in all_results.items():
        for strategy, result in results.items():
            if result is not None:
                result_copy = result.copy()
                result_copy['Signal Source'] = signal_source
                result_copy['Strategy'] = strategy
                all_valid.append(result_copy)
    
    if all_valid:
        all_valid.sort(key=lambda x: x['Total Return (%)'], reverse=True)
        md += f"## 🎯 Overall Best Strategies\n\n"
        md += f"| Rank | Signal + Strategy | Total Return | Max Drawdown | Sharpe | Trades/Year | Time in Market | Win Rate | Parameters |\n"
        md += f"|------|-------------------|--------------|--------------|--------|-------------|----------------|----------|------------|\n"
        for i, result in enumerate(all_valid[:5], 1):
            params = result.get('Params', 'Default')
            md += f"| {i} | **{result['Signal Source']} + {result['Strategy'].upper()}** | {result['Total Return (%)']:.1f}% | {result['Max Drawdown (%)']:.1f}% | {result['Sharpe Ratio']:.2f} | {result['Trades/Year']:.2f} | {result['Time in Market (%)']:.1f}% | {result['Win Rate (%)']:.1f}% | {params} |\n"
        md += f"\n"
    
    # Save to file
    filename = f"strategy_optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, 'w') as f:
        f.write(md)
    
    print(f"\n📁 **Report saved to:** {filename}")
    return filename

# --- CSV Export Functions ---
def save_all_results_csv(all_raw_results):
    """Save all backtest results to CSV for detailed analysis"""
    csv_data = []
    
    for result in all_raw_results:
        csv_data.append({
            'Signal_Source': result['Signal_Source'],
            'Strategy': result['Strategy'],
            'Parameters': result['Parameters'],
            'Total_Return_Pct': result['Total_Return_Pct'],
            'Max_Drawdown_Pct': result['Max_Drawdown_Pct'],
            'Sharpe_Ratio': result['Sharpe_Ratio'],
            'Final_Value': result['Final_Value'],
            'Num_Trades': result.get('Num_Trades', None),
            'Trades_Per_Year': result.get('Trades_Per_Year', None),
            'Time_in_Market_Pct': result.get('Time_in_Market_Pct', None),
            'Win_Rate_Pct': result.get('Win_Rate_Pct', None),
            'Meets_Drawdown_Constraint': result['Meets_Drawdown_Constraint']
        })
    
    df = pd.DataFrame(csv_data)
    
    # Sort by total return descending
    df = df.sort_values('Total_Return_Pct', ascending=False)
    
    # Save to CSV
    filename = f"all_backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"📊 **All results saved to CSV:** {filename}")
    print(f"   Total combinations tested: {len(df)}")
    print(f"   Results meeting constraint: {len(df[df['Meets_Drawdown_Constraint'] == True])}")
    
    return filename

# --- Main Grid Search ---
def main():
    start_date = "2010-12-13"
    end_date = datetime.now().strftime('%Y-%m-%d')
    initial_capital = 55000
    symbols = ['TQQQ', 'QQQ']
    trade_symbol = 'LQQ3.L'
    strategies = ['macd', 'sma', 'or', 'and', 'weighted', 'variable', 'multi']
    max_trades_per_year = 12
    max_time_in_market = 90.0
    
    print("🚀 LQQ3 Trading Strategy Optimization")
    print("=" * 50)
    print(f"Trading Asset: {trade_symbol}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: £{initial_capital:,}")
    print(f"Drawdown Constraint: > -50% (better than -50%)")
    print(f"Trade Constraint: ≤{max_trades_per_year} trades/year")
    print(f"Time in Market Constraint: ≤{max_time_in_market}%")
    print("=" * 50)
    
    print("\n📈 Fetching LQQ3 data...")
    trade_df = fetch_data(trade_symbol, start_date, end_date)
    
    all_results = {}
    all_raw_results = []  # Store every single test result for CSV
    
    for symbol in symbols:
        print(f"\n🔍 Testing {symbol} as signal source...")
        signal_df = fetch_data(symbol, start_date, end_date)
        aligned = align_data(signal_df, trade_df)
        print(f"   Aligned data: {len(aligned)} trading days")
        
        results = {}
        
        for strat in strategies:
            print(f"   Testing {strat}...", end=" ")
            best = None
            
            if strat == 'macd':
                for fast in [8,12,16]:
                    for slow in [20,26,32]:
                        for sig in [7,9,12]:
                            sigs = get_signals(signal_df, 'macd', {'fast':fast,'slow':slow,'signal':sig})
                            sigs = pd.Series(sigs, index=signal_df.index).reindex(aligned.index).fillna(0).astype(int)
                            port = run_backtest(aligned, sigs, initial_capital)
                            m = calc_metrics(port, initial_capital)
                            
                            # Store every result for CSV
                            all_raw_results.append({
                                'Signal_Source': symbol,
                                'Strategy': strat,
                                'Parameters': f"fast={fast}, slow={slow}, signal={sig}",
                                'Total_Return_Pct': m['Total Return (%)'],
                                'Max_Drawdown_Pct': m['Max Drawdown (%)'],
                                'Sharpe_Ratio': m['Sharpe Ratio'],
                                'Final_Value': m['Final Value'],
                                'Num_Trades': m['Num Trades'],
                                'Trades_Per_Year': m['Trades/Year'],
                                'Time_in_Market_Pct': m['Time in Market (%)'],
                                'Win_Rate_Pct': m['Win Rate (%)'],
                                'Meets_Drawdown_Constraint': m['Max Drawdown (%)'] > -50 and m['Trades/Year'] <= max_trades_per_year and m['Time in Market (%)'] <= max_time_in_market
                            })
                            
                            # Filtering for best
                            if m['Max Drawdown (%)'] < -50 or m['Trades/Year'] > max_trades_per_year or m['Time in Market (%)'] > max_time_in_market:
                                continue
                            m['Params'] = f"fast={fast}, slow={slow}, signal={sig}"
                            if not best or m['Total Return (%)'] > best['Total Return (%)']:
                                best = m
                results[strat] = best
                
            elif strat == 'sma':
                for period in [150,200,250]:
                    sigs = get_signals(signal_df, 'sma', {'period':period})
                    sigs = pd.Series(sigs, index=signal_df.index).reindex(aligned.index).fillna(0).astype(int)
                    port = run_backtest(aligned, sigs, initial_capital)
                    m = calc_metrics(port, initial_capital)
                    all_raw_results.append({
                        'Signal_Source': symbol,
                        'Strategy': strat,
                        'Parameters': f"period={period}",
                        'Total_Return_Pct': m['Total Return (%)'],
                        'Max_Drawdown_Pct': m['Max Drawdown (%)'],
                        'Sharpe_Ratio': m['Sharpe Ratio'],
                        'Final_Value': m['Final Value'],
                        'Num_Trades': m['Num Trades'],
                        'Trades_Per_Year': m['Trades/Year'],
                        'Time_in_Market_Pct': m['Time in Market (%)'],
                        'Win_Rate_Pct': m['Win Rate (%)'],
                        'Meets_Drawdown_Constraint': m['Max Drawdown (%)'] > -50 and m['Trades/Year'] <= max_trades_per_year and m['Time in Market (%)'] <= max_time_in_market
                    })
                    if m['Max Drawdown (%)'] < -50 or m['Trades/Year'] > max_trades_per_year or m['Time in Market (%)'] > max_time_in_market:
                        continue
                    m['Params'] = f"period={period}"
                    if not best or m['Total Return (%)'] > best['Total Return (%)']:
                        best = m
                results[strat] = best
                
            elif strat in ['or', 'and', 'variable', 'multi']:
                if strat == 'variable':
                    sigs, alloc = get_signals(signal_df, 'variable', {})
                    sigs = pd.Series(sigs, index=signal_df.index).reindex(aligned.index).fillna(0).astype(int)
                    alloc = pd.Series(alloc, index=signal_df.index).reindex(aligned.index).fillna(0)
                    port = run_backtest(aligned, sigs, initial_capital, allocation=alloc)
                else:
                    sigs = get_signals(signal_df, strat, {})
                    sigs = pd.Series(sigs, index=signal_df.index).reindex(aligned.index).fillna(0).astype(int)
                    port = run_backtest(aligned, sigs, initial_capital)
                m = calc_metrics(port, initial_capital)
                all_raw_results.append({
                    'Signal_Source': symbol,
                    'Strategy': strat,
                    'Parameters': 'Default',
                    'Total_Return_Pct': m['Total Return (%)'],
                    'Max_Drawdown_Pct': m['Max Drawdown (%)'],
                    'Sharpe_Ratio': m['Sharpe Ratio'],
                    'Final_Value': m['Final Value'],
                    'Num_Trades': m['Num Trades'],
                    'Trades_Per_Year': m['Trades/Year'],
                    'Time_in_Market_Pct': m['Time in Market (%)'],
                    'Win_Rate_Pct': m['Win Rate (%)'],
                    'Meets_Drawdown_Constraint': m['Max Drawdown (%)'] > -50 and m['Trades/Year'] <= max_trades_per_year and m['Time in Market (%)'] <= max_time_in_market
                })
                if m['Max Drawdown (%)'] < -50 or m['Trades/Year'] > max_trades_per_year or m['Time in Market (%)'] > max_time_in_market:
                    results[strat] = None
                else:
                    m['Params'] = 'Default'
                    results[strat] = m
                    
            elif strat == 'weighted':
                for macd_weight in [0.4,0.5,0.6,0.7]:
                    sma_weight = 1-macd_weight
                    for threshold in [0.4,0.5,0.6]:
                        sigs = get_signals(signal_df, 'weighted', {'macd_weight':macd_weight,'sma_weight':sma_weight,'threshold':threshold})
                        sigs = pd.Series(sigs, index=signal_df.index).reindex(aligned.index).fillna(0).astype(int)
                        port = run_backtest(aligned, sigs, initial_capital)
                        m = calc_metrics(port, initial_capital)
                        all_raw_results.append({
                            'Signal_Source': symbol,
                            'Strategy': strat,
                            'Parameters': f"MACD={macd_weight}, SMA={sma_weight}, threshold={threshold}",
                            'Total_Return_Pct': m['Total Return (%)'],
                            'Max_Drawdown_Pct': m['Max Drawdown (%)'],
                            'Sharpe_Ratio': m['Sharpe Ratio'],
                            'Final_Value': m['Final Value'],
                            'Num_Trades': m['Num Trades'],
                            'Trades_Per_Year': m['Trades/Year'],
                            'Time_in_Market_Pct': m['Time in Market (%)'],
                            'Win_Rate_Pct': m['Win Rate (%)'],
                            'Meets_Drawdown_Constraint': m['Max Drawdown (%)'] > -50 and m['Trades/Year'] <= max_trades_per_year and m['Time in Market (%)'] <= max_time_in_market
                        })
                        if m['Max Drawdown (%)'] < -50 or m['Trades/Year'] > max_trades_per_year or m['Time in Market (%)'] > max_time_in_market:
                            continue
                        m['Params'] = f"MACD={macd_weight}, SMA={sma_weight}, threshold={threshold}"
                        if not best or m['Total Return (%)'] > best['Total Return (%)']:
                            best = m
                results[strat] = best
            
            # Print quick status
            if results[strat]:
                print(f"✅ {results[strat]['Total Return (%)']:.0f}% return, {results[strat]['Trades/Year']:.1f} trades/year, {results[strat]['Time in Market (%)']:.1f}% in market")
            else:
                print("❌ No valid result")
        
        all_results[symbol] = results
    
    # Generate markdown report
    print(f"\n📝 Generating markdown report...")
    save_markdown_report(all_results, start_date, end_date, initial_capital)
    # Save all results to CSV
    save_all_results_csv(all_raw_results)

if __name__ == "__main__":
    main()
