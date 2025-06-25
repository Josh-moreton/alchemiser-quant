#!/usr/bin/env python3
"""
Variable Allocation Strategy Testing
Test different allocation levels based on signal agreement:
- Both signals SELL: 33% LQQ3, 67% cash
- One signal BUY: 66% LQQ3, 34% cash  
- Both signals BUY: 100% LQQ3

Compare vs current OR logic and buy-and-hold for drawdown and risk metrics.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class VariableAllocationStrategy:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        self.signals = pd.DataFrame()
        self.results = {}
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data for variable allocation strategy testing...")
        
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
        """Calculate MACD and SMA signals with allocation levels"""
        print("Calculating signals and allocation levels...")
        
        tqqq_data = self.data['TQQQ'].copy()
        
        # Calculate MACD components
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Individual signal components
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Signal count and allocation
        tqqq_data['Signal_Count'] = tqqq_data['MACD_Bullish'] + tqqq_data['SMA_Bullish']
        
        # Variable allocation based on signal count
        allocation_map = {0: 0.33, 1: 0.66, 2: 1.00}  # 33%, 66%, 100%
        tqqq_data['Target_Allocation'] = tqqq_data['Signal_Count'].map(allocation_map)
        
        # OR Logic allocation for comparison (original strategy)
        tqqq_data['OR_Allocation'] = np.where(
            (tqqq_data['MACD_Bullish'] == 1) | (tqqq_data['SMA_Bullish'] == 1), 
            1.00, 0.34  # 100% invested or 34% (66% sold)
        )
        
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
                          'MACD_Bullish', 'SMA_Bullish', 'Signal_Count',
                          'Target_Allocation', 'OR_Allocation']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        for col in ['MACD_Bullish', 'SMA_Bullish', 'Signal_Count', 'Target_Allocation', 'OR_Allocation']:
            self.signals[col] = self.signals[col].fillna(method='ffill')
        
        # Drop rows without LQQ3 data
        self.signals = self.signals.dropna(subset=['LQQ3_Close'])
        
        print(f"Signals calculated for {len(self.signals)} trading days")
        return self.signals
    
    def run_strategy_backtest(self, allocation_column, strategy_name):
        """Run backtest for a specific allocation strategy"""
        print(f"Running {strategy_name} backtest...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            target_allocation = row[allocation_column]
            
            # Calculate target portfolio value and required LQQ3 value
            total_portfolio_value = cash + shares * lqq3_price
            target_lqq3_value = total_portfolio_value * target_allocation
            target_shares = target_lqq3_value / lqq3_price
            
            # Execute rebalancing
            shares_diff = target_shares - shares
            
            if abs(shares_diff) > 0.001:  # Only trade if meaningful difference
                if shares_diff > 0:  # Need to buy
                    cost = shares_diff * lqq3_price
                    if cost <= cash:
                        shares += shares_diff
                        cash -= cost
                        trade_type = 'BUY'
                        trade_amount = shares_diff
                    else:
                        # Buy what we can afford
                        affordable_shares = cash / lqq3_price
                        shares += affordable_shares
                        cash = 0
                        trade_type = 'BUY_PARTIAL'
                        trade_amount = affordable_shares
                else:  # Need to sell
                    shares_to_sell = abs(shares_diff)
                    cash += shares_to_sell * lqq3_price
                    shares -= shares_to_sell
                    trade_type = 'SELL'
                    trade_amount = shares_to_sell
            else:
                trade_type = 'HOLD'
                trade_amount = 0
            
            # Calculate final portfolio value and allocation
            portfolio_value = cash + shares * lqq3_price
            actual_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Target_Allocation': target_allocation,
                'Actual_Allocation': actual_allocation,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount,
                'Signal_Count': row['Signal_Count'],
                'MACD_Bullish': row['MACD_Bullish'],
                'SMA_Bullish': row['SMA_Bullish']
            })
        
        portfolio_df = pd.DataFrame(portfolio_data)
        portfolio_df.set_index('Date', inplace=True)
        
        print(f"{strategy_name} backtest completed for {len(portfolio_df)} days")
        return portfolio_df
    
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
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        excess_daily_return = daily_returns.mean() * 252 - risk_free_rate
        sharpe_ratio = excess_daily_return / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = daily_returns[daily_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = excess_daily_return / downside_deviation if downside_deviation != 0 else 0
        
        # Maximum drawdown
        rolling_max = portfolio_df['Portfolio_Value'].expanding().max()
        drawdown = (portfolio_df['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Calmar ratio (Annual return / Max drawdown)
        years = (portfolio_df.index[-1] - portfolio_df.index[0]).days / 365.25
        annual_return = (final_value / self.initial_capital) ** (1/years) - 1
        calmar_ratio = annual_return / abs(max_drawdown/100) if max_drawdown != 0 else 0
        
        # Trading statistics
        trades = portfolio_df[portfolio_df['Trade_Type'].isin(['BUY', 'SELL', 'BUY_PARTIAL'])]
        num_trades = len(trades)
        
        # Allocation statistics
        avg_allocation = portfolio_df['Actual_Allocation'].mean()
        
        # Time in different allocation states
        allocation_distribution = portfolio_df['Target_Allocation'].value_counts(normalize=True) * 100
        
        # Win rate
        win_rate = (daily_returns > 0).mean() * 100 if len(daily_returns) > 0 else 0
        
        metrics = {
            'Strategy': strategy_name,
            'Total Return (%)': round(total_return, 2),
            'Annual Return (%)': round(annual_return * 100, 2),
            'Buy & Hold Return (%)': round(buyhold_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Final Portfolio Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Sortino Ratio': round(sortino_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Calmar Ratio': round(calmar_ratio, 2),
            'Number of Trades': num_trades,
            'Trades per Year': round(num_trades / years, 1),
            'Average Allocation (%)': round(avg_allocation * 100, 1),
            'Win Rate (%)': round(win_rate, 1),
            'Allocation Distribution': allocation_distribution.to_dict()
        }
        
        return metrics, portfolio_df
    
    def run_comparison_analysis(self):
        """Run all strategy variants and compare them"""
        print("\n" + "="*80)
        print("VARIABLE ALLOCATION STRATEGY COMPARISON")
        print("="*80)
        
        # Calculate signals
        self.calculate_signals()
        
        # Strategy definitions
        strategies = {
            'Variable Allocation (33/66/100%)': 'Target_Allocation',
            'OR Logic (Current Strategy)': 'OR_Allocation'
        }
        
        results = {}
        portfolios = {}
        
        # Run each strategy
        for strategy_name, allocation_column in strategies.items():
            portfolio = self.run_strategy_backtest(allocation_column, strategy_name)
            metrics, portfolio_detailed = self.calculate_performance_metrics(portfolio, strategy_name)
            
            results[strategy_name] = metrics
            portfolios[strategy_name] = portfolio_detailed
        
        # Add buy-and-hold for reference
        buyhold_metrics = self.calculate_buyhold_metrics()
        results['Buy & Hold'] = buyhold_metrics
        
        self.results = results
        self.portfolios = portfolios
        
        return results, portfolios
    
    def calculate_buyhold_metrics(self):
        """Calculate buy-and-hold metrics for comparison"""
        first_price = self.signals['LQQ3_Close'].iloc[0]
        last_price = self.signals['LQQ3_Close'].iloc[-1]
        
        total_return = (last_price / first_price - 1) * 100
        final_value = self.initial_capital * (last_price / first_price)
        
        # Calculate daily returns for risk metrics
        daily_returns = self.signals['LQQ3_Close'].pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        years = (self.signals.index[-1] - self.signals.index[0]).days / 365.25
        annual_return = (last_price / first_price) ** (1/years) - 1
        
        # Sharpe ratio
        risk_free_rate = 0.02
        excess_return = annual_return - risk_free_rate
        sharpe_ratio = excess_return / (daily_returns.std() * np.sqrt(252)) if daily_returns.std() != 0 else 0
        
        # Sortino ratio
        negative_returns = daily_returns[daily_returns < 0]
        downside_deviation = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = excess_return / downside_deviation if downside_deviation != 0 else 0
        
        # Maximum drawdown
        cumulative_returns = (1 + daily_returns).cumprod()
        rolling_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Calmar ratio
        calmar_ratio = annual_return / abs(max_drawdown/100) if max_drawdown != 0 else 0
        
        win_rate = (daily_returns > 0).mean() * 100
        
        return {
            'Strategy': 'Buy & Hold',
            'Total Return (%)': round(total_return, 2),
            'Annual Return (%)': round(annual_return * 100, 2),
            'Buy & Hold Return (%)': round(total_return, 2),
            'Excess Return (%)': 0.0,
            'Final Portfolio Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Sortino Ratio': round(sortino_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Calmar Ratio': round(calmar_ratio, 2),
            'Number of Trades': 0,
            'Trades per Year': 0.0,
            'Average Allocation (%)': 100.0,
            'Win Rate (%)': round(win_rate, 1),
            'Allocation Distribution': {1.0: 100.0}
        }
    
    def print_comparison_results(self):
        """Print detailed comparison of all strategies"""
        print("\n" + "="*100)
        print("STRATEGY PERFORMANCE COMPARISON")
        print("="*100)
        
        # Key metrics table
        metrics_to_show = [
            'Total Return (%)', 'Excess Return (%)', 'Volatility (%)', 
            'Sharpe Ratio', 'Sortino Ratio', 'Max Drawdown (%)', 'Calmar Ratio'
        ]
        
        print(f"{'Strategy':<35} {'Total Ret':<10} {'Excess':<8} {'Vol':<6} {'Sharpe':<7} {'Sortino':<7} {'MaxDD':<7} {'Calmar':<7}")
        print("-" * 100)
        
        for strategy_name, metrics in self.results.items():
            print(f"{strategy_name:<35} {metrics['Total Return (%)']:>8.1f}% "
                  f"{metrics['Excess Return (%)']:>6.1f}% {metrics['Volatility (%)']:>4.1f}% "
                  f"{metrics['Sharpe Ratio']:>6.2f} {metrics['Sortino Ratio']:>6.2f} "
                  f"{metrics['Max Drawdown (%)']:>5.1f}% {metrics['Calmar Ratio']:>6.2f}")
        
        print("\n" + "="*100)
        print("DETAILED ANALYSIS")
        print("="*100)
        
        for strategy_name, metrics in self.results.items():
            print(f"\n{strategy_name.upper()}:")
            print("-" * 50)
            print(f"  Final Value: £{metrics['Final Portfolio Value (£)']:,.0f}")
            print(f"  Annual Return: {metrics['Annual Return (%)']:.1f}%")
            print(f"  Number of Trades: {metrics['Number of Trades']}")
            print(f"  Average Allocation: {metrics['Average Allocation (%)']:.1f}%")
            print(f"  Win Rate: {metrics['Win Rate (%)']:.1f}%")
            
            if 'Allocation Distribution' in metrics:
                print(f"  Allocation Distribution:")
                for allocation, percentage in sorted(metrics['Allocation Distribution'].items()):
                    allocation_pct = allocation * 100
                    print(f"    {allocation_pct:3.0f}% allocation: {percentage:5.1f}% of time")
        
        # Key insights
        print(f"\n{'='*100}")
        print("KEY INSIGHTS")
        print("="*100)
        
        variable_metrics = self.results['Variable Allocation (33/66/100%)']
        or_logic_metrics = self.results['OR Logic (Current Strategy)']
        
        print(f"Variable Allocation vs OR Logic:")
        print(f"  Return difference: {variable_metrics['Total Return (%)'] - or_logic_metrics['Total Return (%)']:+.1f}%")
        print(f"  Volatility difference: {variable_metrics['Volatility (%)'] - or_logic_metrics['Volatility (%)']:+.1f}%")
        print(f"  Sharpe ratio difference: {variable_metrics['Sharpe Ratio'] - or_logic_metrics['Sharpe Ratio']:+.2f}")
        print(f"  Sortino ratio difference: {variable_metrics['Sortino Ratio'] - or_logic_metrics['Sortino Ratio']:+.2f}")
        print(f"  Max drawdown difference: {variable_metrics['Max Drawdown (%)'] - or_logic_metrics['Max Drawdown (%)']:+.1f}%")
        
        # Determine winner
        if (variable_metrics['Sharpe Ratio'] > or_logic_metrics['Sharpe Ratio'] and 
            variable_metrics['Max Drawdown (%)'] > or_logic_metrics['Max Drawdown (%)']):
            print(f"\n🏆 WINNER: Variable Allocation Strategy")
            print(f"   Better risk-adjusted returns with lower drawdown")
        elif variable_metrics['Total Return (%)'] > or_logic_metrics['Total Return (%)']:
            print(f"\n🏆 WINNER: Variable Allocation Strategy")
            print(f"   Higher absolute returns")
        else:
            print(f"\n🏆 WINNER: OR Logic Strategy (Current)")
            print(f"   Better overall risk-adjusted performance")
    
    def save_results(self):
        """Save detailed results to CSV files"""
        # Save comparison metrics
        comparison_df = pd.DataFrame(self.results).T
        comparison_df.to_csv('variable_allocation_comparison.csv')
        print(f"\nComparison results saved to 'variable_allocation_comparison.csv'")
        
        # Save detailed portfolio data
        for strategy_name, portfolio_df in self.portfolios.items():
            filename = f"variable_allocation_{strategy_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}_detailed.csv"
            portfolio_df.to_csv(filename)
            print(f"Detailed {strategy_name} results saved to '{filename}'")
    
    def get_current_signal_status(self):
        """Get current signal status and allocation recommendation"""
        if self.signals.empty:
            return None
            
        latest = self.signals.iloc[-1]
        current_date = self.signals.index[-1]
        
        macd_bullish = latest['MACD_Bullish'] == 1
        sma_bullish = latest['SMA_Bullish'] == 1
        signal_count = latest['Signal_Count']
        target_allocation = latest['Target_Allocation']
        
        return {
            'date': current_date,
            'macd_bullish': macd_bullish,
            'sma_bullish': sma_bullish,
            'signal_count': signal_count,
            'target_allocation': target_allocation,
            'tqqq_price': latest['TQQQ_Close'],
            'lqq3_price': latest['LQQ3_Close']
        }

def main():
    """Run the variable allocation strategy analysis"""
    print("="*80)
    print("VARIABLE ALLOCATION STRATEGY TESTING")
    print("="*80)
    print("Testing graduated allocation based on signal agreement:")
    print("• Both signals SELL: 33% LQQ3, 67% cash")
    print("• One signal BUY: 66% LQQ3, 34% cash")
    print("• Both signals BUY: 100% LQQ3")
    print("-"*80)
    
    # Initialize strategy
    strategy = VariableAllocationStrategy(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        # Fetch data
        strategy.fetch_data()
        
        # Run comparison analysis
        results, portfolios = strategy.run_comparison_analysis()
        
        # Display results
        strategy.print_comparison_results()
        
        # Current status
        current_status = strategy.get_current_signal_status()
        if current_status:
            print(f"\n{'='*80}")
            print("CURRENT ALLOCATION RECOMMENDATION")
            print("="*80)
            print(f"Date: {current_status['date'].strftime('%Y-%m-%d')}")
            print(f"MACD Signal: {'🟢 Bullish' if current_status['macd_bullish'] else '🔴 Bearish'}")
            print(f"SMA Signal: {'🟢 Bullish' if current_status['sma_bullish'] else '🔴 Bearish'}")
            print(f"Signal Count: {current_status['signal_count']}/2")
            print(f"Recommended Allocation: {current_status['target_allocation']*100:.0f}% LQQ3")
            print(f"TQQQ Price: ${current_status['tqqq_price']:.2f}")
            print(f"LQQ3 Price: £{current_status['lqq3_price']:.2f}")
        
        # Save results
        strategy.save_results()
        
        return strategy
        
    except Exception as e:
        print(f"Error running variable allocation analysis: {e}")
        return None

if __name__ == "__main__":
    strategy = main()
