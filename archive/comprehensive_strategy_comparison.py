#!/usr/bin/env python3
"""
Comprehensive Strategy Comparison: Original SMA vs OR Logic vs Variable Allocation
Testing all three strategies with detailed risk and performance analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveStrategyComparison:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.results = {}
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data for comprehensive strategy comparison...")
        
        # Fetch TQQQ data (US ETF)
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        
        # Fetch LQQ3.L data (LSE ticker)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data. Please check ticker symbols and date range.")
        
        # Handle multi-level columns
        if tqqq.columns.nlevels > 1:
            tqqq.columns = tqqq.columns.get_level_values(0)
        if lqq3.columns.nlevels > 1:
            lqq3.columns = lqq3.columns.get_level_values(0)
        
        self.data['TQQQ'] = tqqq
        self.data['LQQ3'] = lqq3
        
        print(f"Data fetched: TQQQ {len(tqqq)} days, LQQ3 {len(lqq3)} days")
        return self.data
    
    def calculate_signals(self):
        """Calculate all signal types for comparison"""
        print("Calculating signals for all strategies...")
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD components
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Individual signals
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Strategy signals
        # 1. Original SMA Strategy
        tqqq_data['Original_SMA_Signal'] = tqqq_data['SMA_Bullish']
        
        # 2. OR Logic Strategy (either signal bullish)
        tqqq_data['OR_Logic_Signal'] = ((tqqq_data['MACD_Bullish'] == 1) | 
                                       (tqqq_data['SMA_Bullish'] == 1)).astype(int)
        
        # 3. Variable Allocation Strategy (signal count)
        tqqq_data['Signal_Count'] = tqqq_data['MACD_Bullish'] + tqqq_data['SMA_Bullish']
        
        # Align with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Find common date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter to common dates
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge data
        self.signals = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'MACD', 'MACD_Signal', 'SMA_200',
                          'MACD_Bullish', 'SMA_Bullish', 'Original_SMA_Signal',
                          'OR_Logic_Signal', 'Signal_Count']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        for col in ['MACD_Bullish', 'SMA_Bullish', 'Original_SMA_Signal', 'OR_Logic_Signal', 'Signal_Count']:
            self.signals[col] = self.signals[col].fillna(method='ffill')
        
        # Drop rows without LQQ3 data
        self.signals = self.signals.dropna(subset=['LQQ3_Close'])
        
        print(f"Signals calculated for {len(self.signals)} trading days")
        return self.signals
    
    def run_original_sma_backtest(self):
        """Run backtest for original 200-day SMA strategy"""
        print("Running Original SMA strategy backtest...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['Original_SMA_Signal']
            
            # Calculate position change
            prev_signal = portfolio_data[-1]['Signal'] if portfolio_data else 0
            position_change = signal - prev_signal
            
            # Execute trades
            if position_change > 0:  # Buy signal
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                else:
                    trade_type = 'HOLD'
                    
            elif position_change < 0:  # Sell signal
                if shares > 0:
                    shares_to_sell = shares * 0.66  # Sell 66%
                    cash += shares_to_sell * lqq3_price
                    shares -= shares_to_sell
                    trade_type = 'SELL'
                else:
                    trade_type = 'HOLD'
            else:
                trade_type = 'HOLD'
            
            # Calculate portfolio value
            portfolio_value = cash + shares * lqq3_price
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Signal': signal,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type
            })
        
        return pd.DataFrame(portfolio_data).set_index('Date')
    
    def run_or_logic_backtest(self):
        """Run backtest for OR Logic strategy"""
        print("Running OR Logic strategy backtest...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal = row['OR_Logic_Signal']
            
            # Calculate position change
            prev_signal = portfolio_data[-1]['Signal'] if portfolio_data else 0
            position_change = signal - prev_signal
            
            # Execute trades
            if position_change > 0:  # Buy signal
                if cash > 0:
                    new_shares = cash / lqq3_price
                    shares += new_shares
                    cash = 0
                    trade_type = 'BUY'
                else:
                    trade_type = 'HOLD'
                    
            elif position_change < 0:  # Sell signal
                if shares > 0:
                    shares_to_sell = shares * 0.66  # Sell 66%
                    cash += shares_to_sell * lqq3_price
                    shares -= shares_to_sell
                    trade_type = 'SELL'
                else:
                    trade_type = 'HOLD'
            else:
                trade_type = 'HOLD'
            
            # Calculate portfolio value
            portfolio_value = cash + shares * lqq3_price
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Signal': signal,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type
            })
        
        return pd.DataFrame(portfolio_data).set_index('Date')
    
    def run_variable_allocation_backtest(self):
        """Run backtest for Variable Allocation strategy"""
        print("Running Variable Allocation strategy backtest...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            signal_count = row['Signal_Count']
            
            # Determine target allocation based on signal count
            if signal_count == 0:  # Both signals bearish
                target_allocation = 0.33
            elif signal_count == 1:  # One signal bullish
                target_allocation = 0.66
            else:  # Both signals bullish
                target_allocation = 1.0
            
            # Calculate current allocation
            portfolio_value = cash + shares * lqq3_price
            current_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            # Rebalance if allocation difference is significant (>5%)
            allocation_diff = target_allocation - current_allocation
            
            if abs(allocation_diff) > 0.05:  # 5% threshold to avoid excessive trading
                target_value = portfolio_value * target_allocation
                current_equity_value = shares * lqq3_price
                
                if allocation_diff > 0:  # Need to buy more
                    buy_value = min(cash, target_value - current_equity_value)
                    if buy_value > 0:
                        new_shares = buy_value / lqq3_price
                        shares += new_shares
                        cash -= buy_value
                        trade_type = 'BUY'
                    else:
                        trade_type = 'HOLD'
                else:  # Need to sell some
                    sell_value = min(current_equity_value, current_equity_value - target_value)
                    if sell_value > 0:
                        shares_to_sell = sell_value / lqq3_price
                        shares -= shares_to_sell
                        cash += sell_value
                        trade_type = 'SELL'
                    else:
                        trade_type = 'HOLD'
            else:
                trade_type = 'HOLD'
            
            # Recalculate portfolio value
            portfolio_value = cash + shares * lqq3_price
            actual_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Signal_Count': signal_count,
                'Target_Allocation': target_allocation,
                'Actual_Allocation': actual_allocation,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type
            })
        
        return pd.DataFrame(portfolio_data).set_index('Date')
    
    def calculate_performance_metrics(self, portfolio_df, strategy_name):
        """Calculate comprehensive performance metrics"""
        
        # Calculate returns
        portfolio_df['Daily_Return'] = portfolio_df['Portfolio_Value'].pct_change()
        portfolio_df['Cumulative_Return'] = (portfolio_df['Portfolio_Value'] / self.initial_capital - 1) * 100
        
        # Buy and hold benchmark
        portfolio_df['BuyHold_Value'] = (self.initial_capital * 
                                       portfolio_df['LQQ3_Price'] / 
                                       portfolio_df['LQQ3_Price'].iloc[0])
        portfolio_df['BuyHold_Return'] = (portfolio_df['BuyHold_Value'] / self.initial_capital - 1) * 100
        
        # Performance calculations
        final_value = portfolio_df['Portfolio_Value'].iloc[-1]
        buyhold_final = portfolio_df['BuyHold_Value'].iloc[-1]
        
        total_return = (final_value / self.initial_capital - 1) * 100
        buyhold_return = (buyhold_final / self.initial_capital - 1) * 100
        excess_return = total_return - buyhold_return
        
        # Risk metrics
        daily_returns = portfolio_df['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = daily_returns[daily_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = daily_returns.mean() / downside_deviation * np.sqrt(252) if downside_deviation != 0 else 0
        
        # Maximum drawdown
        rolling_max = portfolio_df['Portfolio_Value'].expanding().max()
        drawdown = (portfolio_df['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Calmar ratio
        years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
        annualized_return = (final_value / self.initial_capital) ** (1/years) - 1
        calmar_ratio = annualized_return / abs(max_drawdown/100) if max_drawdown != 0 else 0
        
        # Trading statistics
        trades = portfolio_df[portfolio_df['Trade_Type'] != 'HOLD']
        num_trades = len(trades)
        
        # Time in market
        if 'Signal' in portfolio_df.columns:
            time_in_market = portfolio_df['Signal'].mean() * 100
        elif 'Actual_Allocation' in portfolio_df.columns:
            time_in_market = portfolio_df['Actual_Allocation'].mean() * 100
        else:
            time_in_market = 0
        
        # Win rate
        if len(daily_returns) > 0:
            win_rate = (daily_returns > 0).mean() * 100
        else:
            win_rate = 0
        
        return {
            'Strategy': strategy_name,
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buyhold_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Annualized Return (%)': round(annualized_return * 100, 2),
            'Final Portfolio Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Sortino Ratio': round(sortino_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Calmar Ratio': round(calmar_ratio, 2),
            'Number of Trades': num_trades,
            'Trades per Year': round(num_trades / years, 1),
            'Time in Market (%)': round(time_in_market, 1),
            'Win Rate (%)': round(win_rate, 1)
        }
    
    def run_all_strategies(self):
        """Run all three strategies and calculate metrics"""
        print("="*80)
        print("COMPREHENSIVE STRATEGY COMPARISON")
        print("="*80)
        
        # Run backtests
        self.results['Original_SMA'] = self.run_original_sma_backtest()
        self.results['OR_Logic'] = self.run_or_logic_backtest()
        self.results['Variable_Allocation'] = self.run_variable_allocation_backtest()
        
        # Calculate metrics
        metrics = {}
        for strategy_name, portfolio_df in self.results.items():
            metrics[strategy_name] = self.calculate_performance_metrics(portfolio_df, strategy_name)
        
        return metrics
    
    def create_comparison_table(self, metrics):
        """Create a formatted comparison table"""
        print("\n" + "="*120)
        print("STRATEGY PERFORMANCE COMPARISON")
        print("="*120)
        
        # Convert to DataFrame for easy formatting
        df = pd.DataFrame(metrics).T
        
        # Key metrics to display
        key_metrics = [
            'Total Return (%)',
            'Excess Return (%)',
            'Annualized Return (%)',
            'Volatility (%)',
            'Sharpe Ratio',
            'Sortino Ratio',
            'Max Drawdown (%)',
            'Calmar Ratio',
            'Number of Trades',
            'Time in Market (%)',
            'Final Portfolio Value (£)'
        ]
        
        print(f"{'Metric':<25} {'Original SMA':<15} {'OR Logic':<15} {'Variable Alloc':<15}")
        print("-" * 120)
        
        for metric in key_metrics:
            if metric in df.columns:
                orig_val = df.loc['Original_SMA', metric]
                or_val = df.loc['OR_Logic', metric]
                var_val = df.loc['Variable_Allocation', metric]
                
                if 'Return' in metric or 'Ratio' in metric or 'Value' in metric:
                    print(f"{metric:<25} {orig_val:<15} {or_val:<15} {var_val:<15}")
                else:
                    print(f"{metric:<25} {orig_val:<15} {or_val:<15} {var_val:<15}")
        
        print("="*120)
        
        # Highlight best performers
        print("\nBEST PERFORMERS:")
        print(f"📈 Highest Total Return: {df['Total Return (%)'].idxmax()} ({df['Total Return (%)'].max():.1f}%)")
        print(f"🎯 Best Sharpe Ratio: {df['Sharpe Ratio'].idxmax()} ({df['Sharpe Ratio'].max():.2f})")
        print(f"🛡️ Best Sortino Ratio: {df['Sortino Ratio'].idxmax()} ({df['Sortino Ratio'].max():.2f})")
        print(f"💪 Lowest Max Drawdown: {df['Max Drawdown (%)'].idxmax()} ({df['Max Drawdown (%)'].max():.1f}%)")
        print(f"⚖️ Best Calmar Ratio: {df['Calmar Ratio'].idxmax()} ({df['Calmar Ratio'].max():.2f})")
        
        return df
    
    def create_portfolio_visualization(self):
        """Create visualization comparing all strategies"""
        print("\nCreating portfolio value comparison chart...")
        
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Strategy Comparison: Original SMA vs OR Logic vs Variable Allocation', 
                     fontsize=16, fontweight='bold')
        
        # Plot 1: Portfolio values over time
        ax1 = axes[0, 0]
        for strategy_name, portfolio_df in self.results.items():
            normalized_values = portfolio_df['Portfolio_Value'] / self.initial_capital
            ax1.plot(portfolio_df.index, normalized_values, 
                    label=strategy_name.replace('_', ' '), linewidth=2)
        
        # Add buy and hold
        buyhold_norm = self.results['Original_SMA']['BuyHold_Value'] / self.initial_capital
        ax1.plot(self.results['Original_SMA'].index, buyhold_norm, 
                label='Buy & Hold', linewidth=1, linestyle='--', alpha=0.7)
        
        ax1.set_title('Portfolio Value Growth (Normalized)')
        ax1.set_ylabel('Portfolio Value (Multiple of Initial)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_yscale('log')
        
        # Plot 2: Drawdowns
        ax2 = axes[0, 1]
        for strategy_name, portfolio_df in self.results.items():
            rolling_max = portfolio_df['Portfolio_Value'].expanding().max()
            drawdown = (portfolio_df['Portfolio_Value'] - rolling_max) / rolling_max * 100
            ax2.fill_between(portfolio_df.index, drawdown, 0, alpha=0.3, 
                           label=strategy_name.replace('_', ' '))
        
        ax2.set_title('Drawdown Comparison')
        ax2.set_ylabel('Drawdown (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Rolling Sharpe ratios
        ax3 = axes[1, 0]
        for strategy_name, portfolio_df in self.results.items():
            returns = portfolio_df['Daily_Return'].dropna()
            rolling_sharpe = returns.rolling(252).mean() / returns.rolling(252).std() * np.sqrt(252)
            ax3.plot(rolling_sharpe.index, rolling_sharpe, 
                    label=strategy_name.replace('_', ' '), alpha=0.8)
        
        ax3.set_title('Rolling 1-Year Sharpe Ratio')
        ax3.set_ylabel('Sharpe Ratio')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Plot 4: Allocation comparison (for Variable Allocation strategy)
        ax4 = axes[1, 1]
        var_portfolio = self.results['Variable_Allocation']
        
        # Show signal counts and allocations
        signal_data = self.signals.tail(252)  # Last year
        ax4.scatter(signal_data.index, signal_data['Signal_Count'], 
                   c=signal_data['Signal_Count'], cmap='RdYlGn', alpha=0.6, s=20)
        ax4.set_title('Variable Allocation Signal Strength (Last Year)')
        ax4.set_ylabel('Number of Bullish Signals')
        ax4.set_ylim(-0.5, 2.5)
        ax4.grid(True, alpha=0.3)
        
        # Add colorbar
        cbar = plt.colorbar(ax4.collections[0], ax=ax4)
        cbar.set_label('Signal Strength')
        
        plt.tight_layout()
        plt.savefig('comprehensive_strategy_comparison.png', dpi=300, bbox_inches='tight')
        print("Visualization saved as 'comprehensive_strategy_comparison.png'")
        plt.show()
    
    def create_detailed_analysis(self, metrics_df):
        """Create detailed analysis of strategy differences"""
        print("\n" + "="*80)
        print("DETAILED STRATEGY ANALYSIS")
        print("="*80)
        
        # Risk-adjusted return analysis
        print("\nRISK-ADJUSTED RETURNS:")
        print("-" * 40)
        
        for strategy in metrics_df.index:
            total_ret = metrics_df.loc[strategy, 'Total Return (%)']
            sharpe = metrics_df.loc[strategy, 'Sharpe Ratio']
            sortino = metrics_df.loc[strategy, 'Sortino Ratio']
            calmar = metrics_df.loc[strategy, 'Calmar Ratio']
            
            print(f"{strategy.replace('_', ' '):<20}: Return {total_ret:>7.1f}% | "
                  f"Sharpe {sharpe:>5.2f} | Sortino {sortino:>5.2f} | Calmar {calmar:>5.2f}")
        
        # Trade frequency analysis
        print("\nTRADE FREQUENCY ANALYSIS:")
        print("-" * 40)
        
        for strategy in metrics_df.index:
            trades = metrics_df.loc[strategy, 'Number of Trades']
            trades_per_year = metrics_df.loc[strategy, 'Trades per Year']
            time_in_market = metrics_df.loc[strategy, 'Time in Market (%)']
            
            print(f"{strategy.replace('_', ' '):<20}: {trades:>3} trades | "
                  f"{trades_per_year:>5.1f}/year | {time_in_market:>5.1f}% in market")
        
        # Current signal status
        print("\nCURRENT SIGNAL STATUS:")
        print("-" * 40)
        
        latest = self.signals.iloc[-1]
        current_date = self.signals.index[-1]
        
        print(f"Date: {current_date.strftime('%Y-%m-%d')}")
        print(f"TQQQ Price: ${latest['TQQQ_Close']:.2f}")
        print(f"200-day SMA: ${latest['SMA_200']:.2f}")
        print(f"MACD: {latest['MACD']:.4f}")
        print(f"MACD Signal: {latest['MACD_Signal']:.4f}")
        
        macd_status = "Bullish" if latest['MACD_Bullish'] else "Bearish"
        sma_status = "Bullish" if latest['SMA_Bullish'] else "Bearish"
        
        print(f"\nIndividual Signals:")
        print(f"  MACD: {macd_status}")
        print(f"  SMA:  {sma_status}")
        
        print(f"\nStrategy Positions:")
        print(f"  Original SMA: {'BUY' if latest['Original_SMA_Signal'] else 'SELL (66% reduction)'}")
        print(f"  OR Logic: {'BUY' if latest['OR_Logic_Signal'] else 'SELL (66% reduction)'}")
        
        signal_count = latest['Signal_Count']
        if signal_count == 0:
            var_alloc = "33% LQQ3, 67% Cash"
        elif signal_count == 1:
            var_alloc = "66% LQQ3, 34% Cash"
        else:
            var_alloc = "100% LQQ3"
        
        print(f"  Variable Allocation: {var_alloc} (Signal Count: {signal_count})")
        
        # Strategy recommendations
        print("\nSTRATEGY RECOMMENDATIONS:")
        print("-" * 40)
        
        best_return = metrics_df['Total Return (%)'].idxmax()
        best_sharpe = metrics_df['Sharpe Ratio'].idxmax()
        best_sortino = metrics_df['Sortino Ratio'].idxmax()
        lowest_drawdown = metrics_df['Max Drawdown (%)'].idxmax()
        
        print(f"🎯 For Maximum Returns: {best_return.replace('_', ' ')}")
        print(f"⚖️ For Best Risk-Adjusted Returns: {best_sharpe.replace('_', ' ')}")
        print(f"🛡️ For Downside Protection: {best_sortino.replace('_', ' ')}")
        print(f"💪 For Lowest Drawdowns: {lowest_drawdown.replace('_', ' ')}")
        
        # Save detailed results
        for strategy_name, portfolio_df in self.results.items():
            filename = f"{strategy_name.lower()}_detailed_results.csv"
            portfolio_df.to_csv(filename)
            print(f"\n{strategy_name} detailed results saved to '{filename}'")
        
        return metrics_df

def main():
    """Run comprehensive strategy comparison"""
    print("="*80)
    print("COMPREHENSIVE STRATEGY COMPARISON")
    print("Original SMA vs OR Logic vs Variable Allocation")
    print("="*80)
    
    # Initialize comparison
    comparison = ComprehensiveStrategyComparison(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        # Run complete analysis
        comparison.fetch_data()
        comparison.calculate_signals()
        metrics = comparison.run_all_strategies()
        
        # Create comparison table
        metrics_df = comparison.create_comparison_table(metrics)
        
        # Create visualizations
        comparison.create_portfolio_visualization()
        
        # Detailed analysis
        comparison.create_detailed_analysis(metrics_df)
        
        # Save summary
        metrics_df.to_csv('comprehensive_strategy_metrics.csv')
        print(f"\nStrategy metrics saved to 'comprehensive_strategy_metrics.csv'")
        
        return comparison, metrics_df
        
    except Exception as e:
        print(f"Error running comprehensive comparison: {e}")
        return None, None

if __name__ == "__main__":
    comparison, metrics = main()
