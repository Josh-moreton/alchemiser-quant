#!/usr/bin/env python3
"""
Enhanced LQQ3 Trading Strategy Backtest
Tests multiple execution timing scenarios:
1. Trade at LQQ3 open (next day after TQQQ signal)
2. Trade at LQQ3 close (next day after TQQQ signal)
3. Trade at LQQ3 intraday price (midpoint between open/close)
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class EnhancedTradingBacktest:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=10000):
        """
        Initialize the enhanced backtesting system
        
        Parameters:
        start_date (str): Start date for backtesting (YYYY-MM-DD)
        end_date (str): End date for backtesting (YYYY-MM-DD), defaults to today
        initial_capital (float): Initial portfolio value
        """
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.results = {}
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("📊 Fetching historical data...")
        
        # Fetch TQQQ data (US ETF)
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        
        # Fetch LQQ3.L data (LSE ticker)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data. Please check ticker symbols and date range.")
        
        # Handle multi-level columns that yfinance sometimes returns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        if lqq3.columns.nlevels > 1:
            lqq3.columns = lqq3.columns.get_level_values(0)
        
        # Store data
        self.data['TQQQ'] = tqqq
        self.data['LQQ3'] = lqq3
        
        print(f"✅ Data fetched successfully:")
        print(f"   TQQQ: {len(tqqq)} days ({tqqq.index.min().date()} to {tqqq.index.max().date()})")
        print(f"   LQQ3: {len(lqq3)} days ({lqq3.index.min().date()} to {lqq3.index.max().date()})")
        
        return self.data
    
    def calculate_signals(self):
        """Calculate trading signals based on TQQQ's 200-day SMA and MACD"""
        print("📈 Calculating trading signals...")
        
        # Calculate indicators for TQQQ
        tqqq_data = self.data['TQQQ'].copy()
        
        # 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        tqqq_data['SMA_Signal'] = np.where(tqqq_data['Close'] > tqqq_data['SMA_200'], 1, 0)
        
        # MACD (12, 26, 9)
        exp1 = tqqq_data['Close'].ewm(span=12).mean()
        exp2 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = exp1 - exp2
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        tqqq_data['MACD_Bullish'] = np.where(tqqq_data['MACD'] > tqqq_data['MACD_Signal'], 1, 0)
        
        # Combined signals for Binary Exit with Laddered Entry strategy
        tqqq_data['Bullish_Count'] = tqqq_data['SMA_Signal'] + tqqq_data['MACD_Bullish']
        
        # Allocation based on number of bullish signals
        # 0 signals = 33% LQQ3, 1 signal = 66% LQQ3, 2 signals = 100% LQQ3
        def get_allocation(count):
            if count == 0:
                return 0.33
            elif count == 1:
                return 0.66
            else:  # count == 2
                return 1.0
        
        tqqq_data['Target_Allocation'] = tqqq_data['Bullish_Count'].apply(get_allocation)
        
        # Calculate position changes
        tqqq_data['Allocation_Change'] = tqqq_data['Target_Allocation'].diff()
        
        # Align with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Create intraday price (midpoint between open and close)
        lqq3_data['Intraday_Price'] = (lqq3_data['Open'] + lqq3_data['Close']) / 2
        
        # Get common date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter to common dates
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge data
        signals_df = pd.merge(
            lqq3_filtered[['Open', 'Close', 'Intraday_Price']].rename(columns={
                'Open': 'LQQ3_Open',
                'Close': 'LQQ3_Close',
                'Intraday_Price': 'LQQ3_Intraday'
            }),
            tqqq_filtered[['Close', 'SMA_200', 'SMA_Signal', 'MACD_Bullish', 
                          'Bullish_Count', 'Target_Allocation', 'Allocation_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill signals for missing data
        fill_columns = ['SMA_Signal', 'MACD_Bullish', 'Bullish_Count', 'Target_Allocation', 'TQQQ_Close', 'SMA_200']
        for col in fill_columns:
            signals_df[col] = signals_df[col].fillna(method='ffill')
        
        signals_df['Allocation_Change'] = signals_df['Allocation_Change'].fillna(0)
        
        # Drop rows where we don't have LQQ3 price data
        self.signals = signals_df.dropna(subset=['LQQ3_Open', 'LQQ3_Close'])
        
        print(f"✅ Signals calculated for {len(self.signals)} trading days")
        print(f"   Date range: {self.signals.index.min().date()} to {self.signals.index.max().date()}")
        
        return self.signals
    
    def run_backtest_scenario(self, execution_price='open', scenario_name='Open Execution'):
        """
        Run backtest for a specific execution timing scenario
        
        Parameters:
        execution_price (str): 'open', 'close', or 'intraday'
        scenario_name (str): Name for this scenario
        """
        print(f"🔄 Running backtest: {scenario_name}")
        
        if self.signals.empty:
            raise ValueError("No signals found. Run calculate_signals() first.")
        
        # Choose the execution price column
        price_columns = {
            'open': 'LQQ3_Open',
            'close': 'LQQ3_Close',
            'intraday': 'LQQ3_Intraday'
        }
        
        if execution_price not in price_columns:
            raise ValueError(f"execution_price must be one of {list(price_columns.keys())}")
        
        price_col = price_columns[execution_price]
        
        # Initialize portfolio tracking
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            # Use the specified execution price
            lqq3_price = row[price_col]
            target_allocation = row['Target_Allocation']
            allocation_change = row['Allocation_Change']
            
            # Current portfolio value before trades
            current_value = cash + shares * lqq3_price
            
            # Determine if we need to rebalance
            current_allocation = (shares * lqq3_price) / current_value if current_value > 0 else 0
            
            trade_type = 'HOLD'
            trade_amount = 0
            
            # Rebalance if allocation changed significantly (>1% difference)
            if abs(current_allocation - target_allocation) > 0.01:
                # Calculate target position
                target_value = current_value * target_allocation
                target_shares = target_value / lqq3_price
                
                if target_shares > shares:
                    # Buy more shares
                    shares_to_buy = target_shares - shares
                    cost = shares_to_buy * lqq3_price
                    if cash >= cost:
                        shares += shares_to_buy
                        cash -= cost
                        trade_type = 'BUY'
                        trade_amount = shares_to_buy
                elif target_shares < shares:
                    # Sell shares
                    shares_to_sell = shares - target_shares
                    proceeds = shares_to_sell * lqq3_price
                    shares -= shares_to_sell
                    cash += proceeds
                    trade_type = 'SELL'
                    trade_amount = shares_to_sell
            
            # Final portfolio value
            portfolio_value = cash + shares * lqq3_price
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'TQQQ_Price': row['TQQQ_Close'],
                'SMA_Signal': row['SMA_Signal'],
                'MACD_Signal': row['MACD_Bullish'],
                'Bullish_Count': row['Bullish_Count'],
                'Target_Allocation': target_allocation,
                'Actual_Allocation': (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount
            })
        
        portfolio_df = pd.DataFrame(portfolio_data)
        portfolio_df.set_index('Date', inplace=True)
        
        # Calculate performance metrics
        portfolio_df['Daily_Return'] = portfolio_df['Portfolio_Value'].pct_change()
        portfolio_df['Cumulative_Return'] = (portfolio_df['Portfolio_Value'] / self.initial_capital - 1) * 100
        
        # Buy and hold benchmark
        portfolio_df['BuyHold_Value'] = (self.initial_capital * 
                                       portfolio_df['LQQ3_Price'] / 
                                       portfolio_df['LQQ3_Price'].iloc[0])
        portfolio_df['BuyHold_Return'] = (portfolio_df['BuyHold_Value'] / self.initial_capital - 1) * 100
        
        # Store results
        self.results[scenario_name] = {
            'portfolio': portfolio_df,
            'execution_price': execution_price,
            'metrics': self.calculate_metrics(portfolio_df)
        }
        
        print(f"✅ {scenario_name} backtest completed")
        return portfolio_df
    
    def calculate_metrics(self, portfolio_df):
        """Calculate performance metrics for a portfolio"""
        daily_returns = portfolio_df['Daily_Return'].dropna()
        
        # Basic metrics
        total_return = (portfolio_df['Portfolio_Value'].iloc[-1] / self.initial_capital - 1) * 100
        buy_hold_return = (portfolio_df['BuyHold_Value'].iloc[-1] / self.initial_capital - 1) * 100
        
        # Risk metrics
        volatility = daily_returns.std() * np.sqrt(252) * 100  # Annualized
        sharpe_ratio = (daily_returns.mean() * 252) / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0
        
        # Drawdown
        cumulative = (1 + daily_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        max_drawdown = drawdown.min() * 100
        
        # Win rate
        winning_days = (daily_returns > 0).sum()
        total_days = len(daily_returns)
        win_rate = (winning_days / total_days * 100) if total_days > 0 else 0
        
        return {
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buy_hold_return, 2),
            'Excess Return (%)': round(total_return - buy_hold_return, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 3),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Win Rate (%)': round(win_rate, 2),
            'Total Trades': (portfolio_df['Trade_Type'] != 'HOLD').sum(),
            'Final Value ($)': round(portfolio_df['Portfolio_Value'].iloc[-1], 2)
        }
    
    def run_all_scenarios(self):
        """Run backtests for all execution timing scenarios"""
        print("🚀 Running all execution timing scenarios...\n")
        
        scenarios = [
            ('open', 'Open Execution (8am UK)'),
            ('close', 'Close Execution (4:30pm UK)'),
            ('intraday', 'Intraday Execution (Midpoint)')
        ]
        
        for execution_price, scenario_name in scenarios:
            self.run_backtest_scenario(execution_price, scenario_name)
            print()
        
        return self.results
    
    def compare_scenarios(self):
        """Compare performance across all scenarios"""
        if not self.results:
            raise ValueError("No results found. Run run_all_scenarios() first.")
        
        print("📊 EXECUTION TIMING COMPARISON")
        print("=" * 60)
        
        # Create comparison table
        comparison_data = []
        for scenario_name, result in self.results.items():
            metrics = result['metrics'].copy()
            metrics['Scenario'] = scenario_name
            comparison_data.append(metrics)
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.set_index('Scenario')
        
        # Display formatted table
        for scenario in comparison_df.index:
            print(f"\n🎯 {scenario}")
            print("-" * 40)
            for metric, value in comparison_df.loc[scenario].items():
                if isinstance(value, (int, float)):
                    if metric in ['Total Return (%)', 'Excess Return (%)', 'Max Drawdown (%)']:
                        print(f"   {metric:<25}: {value:>8.2f}%")
                    elif metric == 'Sharpe Ratio':
                        print(f"   {metric:<25}: {value:>8.3f}")
                    elif metric == 'Final Value ($)':
                        print(f"   {metric:<25}: ${value:>8,.0f}")
                    else:
                        print(f"   {metric:<25}: {value:>8.2f}")
                else:
                    print(f"   {metric:<25}: {value}")
        
        # Highlight best performers
        print(f"\n🏆 BEST PERFORMERS")
        print("-" * 30)
        best_return = comparison_df['Total Return (%)'].idxmax()
        best_sharpe = comparison_df['Sharpe Ratio'].idxmax()
        best_drawdown = comparison_df['Max Drawdown (%)'].idxmax()  # Highest (least negative)
        
        print(f"Highest Return: {best_return} ({comparison_df.loc[best_return, 'Total Return (%)']:.2f}%)")
        print(f"Best Sharpe:    {best_sharpe} ({comparison_df.loc[best_sharpe, 'Sharpe Ratio']:.3f})")
        print(f"Best Drawdown:  {best_drawdown} ({comparison_df.loc[best_drawdown, 'Max Drawdown (%)']:.2f}%)")
        
        return comparison_df
    
    def plot_performance(self):
        """Plot performance comparison across scenarios"""
        if not self.results:
            raise ValueError("No results found. Run run_all_scenarios() first.")
        
        plt.figure(figsize=(15, 10))
        
        # Performance comparison
        plt.subplot(2, 2, 1)
        for scenario_name, result in self.results.items():
            portfolio = result['portfolio']
            plt.plot(portfolio.index, portfolio['Cumulative_Return'], 
                    label=scenario_name, linewidth=2)
        
        plt.title('Cumulative Returns Comparison', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Return (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Drawdown comparison
        plt.subplot(2, 2, 2)
        for scenario_name, result in self.results.items():
            portfolio = result['portfolio']
            daily_returns = portfolio['Daily_Return'].dropna()
            cumulative = (1 + daily_returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max * 100
            plt.plot(portfolio.index[1:], drawdown, 
                    label=scenario_name, linewidth=2)
        
        plt.title('Drawdown Comparison', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Drawdown (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Metrics comparison
        plt.subplot(2, 2, 3)
        metrics_data = []
        scenarios = []
        for scenario_name, result in self.results.items():
            metrics_data.append([
                result['metrics']['Total Return (%)'],
                result['metrics']['Sharpe Ratio'] * 20,  # Scale for visibility
                result['metrics']['Max Drawdown (%)']
            ])
            scenarios.append(scenario_name.replace(' Execution', '').replace(' (', '\n('))
        
        x = np.arange(len(scenarios))
        width = 0.25
        
        plt.bar(x - width, [m[0] for m in metrics_data], width, label='Total Return (%)', alpha=0.8)
        plt.bar(x, [m[1] for m in metrics_data], width, label='Sharpe Ratio (×20)', alpha=0.8)
        plt.bar(x + width, [m[2] for m in metrics_data], width, label='Max Drawdown (%)', alpha=0.8)
        
        plt.title('Key Metrics Comparison', fontsize=14, fontweight='bold')
        plt.xlabel('Execution Timing')
        plt.ylabel('Value')
        plt.xticks(x, scenarios)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Allocation over time (for first scenario)
        plt.subplot(2, 2, 4)
        first_scenario = list(self.results.values())[0]
        portfolio = first_scenario['portfolio']
        plt.plot(portfolio.index, portfolio['Target_Allocation'] * 100, 
                label='Target Allocation', linewidth=2)
        plt.plot(portfolio.index, portfolio['Actual_Allocation'] * 100, 
                label='Actual Allocation', linewidth=1, alpha=0.7)
        
        plt.title('Portfolio Allocation Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('LQQ3 Allocation (%)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

def main():
    """Run the enhanced backtest analysis"""
    print("🎯 LQQ3 Enhanced Execution Timing Backtest")
    print("=" * 50)
    
    # Initialize backtest
    backtest = EnhancedTradingBacktest(
        start_date="2015-01-01",  # Start when LQQ3 has good data
        initial_capital=10000
    )
    
    try:
        # Fetch data and calculate signals
        backtest.fetch_data()
        backtest.calculate_signals()
        
        # Run all scenarios
        backtest.run_all_scenarios()
        
        # Compare results
        comparison_df = backtest.compare_scenarios()
        
        # Plot results
        backtest.plot_performance()
        
        # Save results to CSV
        print(f"\n💾 Saving detailed results...")
        for scenario_name, result in backtest.results.items():
            filename = f"execution_timing_{scenario_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.csv"
            result['portfolio'].to_csv(filename)
            print(f"   Saved: {filename}")
        
        comparison_df.to_csv("execution_timing_comparison.csv")
        print(f"   Saved: execution_timing_comparison.csv")
        
        print(f"\n✅ Analysis complete! Check the CSV files for detailed results.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    main()
