#!/usr/bin/env python3
"""
Laddering Strategy Insights and Optimal Approach Analysis
Detailed analysis of symmetric vs asymmetric allocation strategies
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class OptimalLadderingAnalysis:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data for optimal laddering analysis...")
        
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
        
        return self.data
    
    def calculate_signals(self):
        """Calculate MACD and SMA signals"""
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
        
        # Count bullish signals
        tqqq_data['Bullish_Count'] = tqqq_data['MACD_Bullish'] + tqqq_data['SMA_Bullish']
        
        # Signal changes
        tqqq_data['Count_Change'] = tqqq_data['Bullish_Count'].diff()
        
        # Align with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Find common date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter to common dates
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        # Merge data
        signals_df = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'MACD', 'MACD_Signal', 'SMA_200',
                          'MACD_Bullish', 'SMA_Bullish', 'Bullish_Count', 'Count_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        for col in ['MACD_Bullish', 'SMA_Bullish', 'Bullish_Count']:
            signals_df[col] = signals_df[col].fillna(method='ffill')
        signals_df['Count_Change'] = signals_df['Count_Change'].fillna(0)
        
        # Drop rows without LQQ3 data
        signals_df = signals_df.dropna(subset=['LQQ3_Close'])
        
        return signals_df
    
    def run_binary_exit_strategy(self, signals):
        """Test strategy: Ladder in (33%→66%→100%) but binary exit (100%→33% or 0%)"""
        print("Running binary exit strategy...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            bullish_count = row['Bullish_Count']
            count_change = row['Count_Change']
            
            # Current portfolio value and allocation
            portfolio_value = cash + shares * lqq3_price
            current_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            trade_type = 'HOLD'
            trade_amount = 0
            
            # BUY LOGIC: Ladder in based on signal strength
            if count_change > 0:  # Signal improved
                if bullish_count == 1:  # 0 -> 1 signal: go to 66%
                    target_allocation = 0.66
                elif bullish_count == 2:  # 1 -> 2 signals: go to 100%
                    target_allocation = 1.0
                else:
                    target_allocation = current_allocation
                
                if target_allocation > current_allocation:
                    target_equity_value = portfolio_value * target_allocation
                    target_shares = target_equity_value / lqq3_price
                    shares_to_buy = target_shares - shares
                    
                    cost = shares_to_buy * lqq3_price
                    if cash >= cost:
                        shares += shares_to_buy
                        cash -= cost
                        trade_type = 'BUY'
                        trade_amount = shares_to_buy
                    else:
                        shares_to_buy = cash / lqq3_price
                        shares += shares_to_buy
                        cash = 0
                        trade_type = 'BUY'
                        trade_amount = shares_to_buy
            
            # SELL LOGIC: Binary exit - if any signal deteriorates from a high allocation, exit to minimum
            elif count_change < 0:  # Signal deteriorated
                # If we're highly allocated (66%+ ) and lose any signal, exit to minimum
                if current_allocation >= 0.6:
                    target_allocation = 0.33
                else:
                    target_allocation = current_allocation
                
                if target_allocation < current_allocation:
                    target_equity_value = portfolio_value * target_allocation
                    target_shares = target_equity_value / lqq3_price
                    shares_to_sell = shares - target_shares
                    
                    if shares >= shares_to_sell:
                        shares -= shares_to_sell
                        cash += shares_to_sell * lqq3_price
                        trade_type = 'SELL'
                        trade_amount = shares_to_sell
                    else:
                        cash += shares * lqq3_price
                        trade_amount = shares
                        shares = 0
                        trade_type = 'SELL'
            
            # Calculate final values
            portfolio_value = cash + shares * lqq3_price
            equity_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Bullish_Count': bullish_count,
                'Equity_Allocation': equity_allocation,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount
            })
        
        return pd.DataFrame(portfolio_data)
    
    def run_pure_binary_strategy(self, signals):
        """Test strategy: 100% when any signal bullish, 33% when both bearish"""
        print("Running pure binary strategy...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            bullish_count = row['Bullish_Count']
            count_change = row['Count_Change']
            
            # Simple binary allocation
            if bullish_count > 0:
                target_allocation = 1.0  # 100% if any signal bullish
            else:
                target_allocation = 0.33  # 33% if both bearish
            
            # Current values
            portfolio_value = cash + shares * lqq3_price
            current_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            trade_type = 'HOLD'
            trade_amount = 0
            
            # Execute rebalancing if needed
            if abs(target_allocation - current_allocation) > 0.05:  # Only rebalance if significant difference
                target_equity_value = portfolio_value * target_allocation
                target_shares = target_equity_value / lqq3_price
                shares_diff = target_shares - shares
                
                if shares_diff > 0:  # Need to buy
                    cost = shares_diff * lqq3_price
                    if cash >= cost:
                        shares += shares_diff
                        cash -= cost
                        trade_type = 'BUY'
                        trade_amount = shares_diff
                    else:
                        shares_to_buy = cash / lqq3_price
                        shares += shares_to_buy
                        cash = 0
                        trade_type = 'BUY'
                        trade_amount = shares_to_buy
                else:  # Need to sell
                    shares_to_sell = abs(shares_diff)
                    if shares >= shares_to_sell:
                        shares -= shares_to_sell
                        cash += shares_to_sell * lqq3_price
                        trade_type = 'SELL'
                        trade_amount = shares_to_sell
                    else:
                        cash += shares * lqq3_price
                        trade_amount = shares
                        shares = 0
                        trade_type = 'SELL'
            
            # Calculate final values
            portfolio_value = cash + shares * lqq3_price
            equity_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Bullish_Count': bullish_count,
                'Target_Allocation': target_allocation,
                'Equity_Allocation': equity_allocation,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount
            })
        
        return pd.DataFrame(portfolio_data)
    
    def calculate_performance_metrics(self, portfolio, strategy_name):
        """Calculate performance metrics for a strategy"""
        portfolio = portfolio.copy()
        portfolio.set_index('Date', inplace=True)
        
        # Calculate returns
        portfolio['Daily_Return'] = portfolio['Portfolio_Value'].pct_change()
        
        # Buy and hold benchmark
        portfolio['BuyHold_Value'] = (self.initial_capital * 
                                     portfolio['LQQ3_Price'] / 
                                     portfolio['LQQ3_Price'].iloc[0])
        
        # Performance calculations
        final_value = portfolio['Portfolio_Value'].iloc[-1]
        buyhold_final = portfolio['BuyHold_Value'].iloc[-1]
        
        total_return = (final_value / self.initial_capital - 1) * 100
        buyhold_return = (buyhold_final / self.initial_capital - 1) * 100
        excess_return = total_return - buyhold_return
        
        # Risk metrics
        daily_returns = portfolio['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Sortino ratio
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252)
        sortino_ratio = (daily_returns.mean() * 252) / downside_std if downside_std != 0 else 0
        
        # Maximum drawdown
        rolling_max = portfolio['Portfolio_Value'].expanding().max()
        drawdown = (portfolio['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Trading statistics
        trades = portfolio[portfolio['Trade_Type'] != 'HOLD']
        num_trades = len(trades)
        
        # Time in market
        avg_allocation = portfolio['Equity_Allocation'].mean()
        
        years = (portfolio.index[-1] - portfolio.index[0]).days / 365.25
        
        return {
            'Strategy': strategy_name,
            'Total Return (%)': round(total_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Final Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Sortino Ratio': round(sortino_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Trades per Year': round(num_trades / years, 1),
            'Avg Allocation (%)': round(avg_allocation * 100, 1),
            'portfolio': portfolio
        }
    
    def analyze_exit_strategies(self):
        """Compare different exit strategies"""
        print("="*80)
        print("EXIT STRATEGY ANALYSIS")
        print("="*80)
        
        # Fetch data and calculate signals
        self.fetch_data()
        signals = self.calculate_signals()
        
        # Run different strategies
        binary_exit_portfolio = self.run_binary_exit_strategy(signals)
        pure_binary_portfolio = self.run_pure_binary_strategy(signals)
        
        # Calculate performance metrics
        binary_exit_metrics = self.calculate_performance_metrics(binary_exit_portfolio, "Binary Exit (Ladder In)")
        pure_binary_metrics = self.calculate_performance_metrics(pure_binary_portfolio, "Pure Binary (OR Logic)")
        
        # Also load previous results for comparison
        try:
            symmetric_df = pd.read_csv('symmetric_laddering_results.csv')
            symmetric_df['Date'] = pd.to_datetime(symmetric_df['Date'])
            symmetric_metrics = self.calculate_performance_metrics(symmetric_df, "Symmetric Laddering")
        except:
            symmetric_metrics = None
        
        # Display comparison
        strategies = [binary_exit_metrics, pure_binary_metrics]
        if symmetric_metrics:
            strategies.append(symmetric_metrics)
        
        print(f"\nPERFORMANCE COMPARISON:")
        print("-"*80)
        
        # Print comparison table
        metrics_order = ['Total Return (%)', 'Excess Return (%)', 'Volatility (%)', 
                        'Sharpe Ratio', 'Sortino Ratio', 'Max Drawdown (%)', 'Number of Trades', 'Avg Allocation (%)']
        
        print(f"{'Metric':<20}", end="")
        for strategy in strategies:
            print(f"{strategy['Strategy'][:18]:<20}", end="")
        print()
        print("-"*80)
        
        for metric in metrics_order:
            print(f"{metric:<20}", end="")
            for strategy in strategies:
                value = strategy[metric]
                if isinstance(value, (int, float)):
                    if 'Return' in metric or 'Volatility' in metric or 'Drawdown' in metric:
                        print(f"{value:>18.1f}%", end="  ")
                    elif 'Ratio' in metric:
                        print(f"{value:>19.2f}", end=" ")
                    else:
                        print(f"{value:>19.1f}", end=" ")
                else:
                    print(f"{str(value):>19}", end=" ")
            print()
        
        print("\n" + "="*80)
        print("KEY INSIGHTS FROM EXIT STRATEGY ANALYSIS")
        print("="*80)
        
        # Analysis insights
        print("\n1. LADDERING vs BINARY ALLOCATION:")
        
        if len(strategies) >= 2:
            ladder_sharpe = binary_exit_metrics['Sharpe Ratio']
            binary_sharpe = pure_binary_metrics['Sharpe Ratio']
            
            ladder_return = binary_exit_metrics['Total Return (%)']
            binary_return = pure_binary_metrics['Total Return (%)']
            
            ladder_drawdown = abs(binary_exit_metrics['Max Drawdown (%)'])
            binary_drawdown = abs(pure_binary_metrics['Max Drawdown (%)'])
            
            print(f"   • Laddering Sharpe Ratio: {ladder_sharpe:.2f}")
            print(f"   • Binary Sharpe Ratio: {binary_sharpe:.2f}")
            print(f"   • Laddering Max Drawdown: {ladder_drawdown:.1f}%")
            print(f"   • Binary Max Drawdown: {binary_drawdown:.1f}%")
            
            if ladder_sharpe > binary_sharpe:
                print(f"   ✓ Laddering provides better risk-adjusted returns")
            else:
                print(f"   ✓ Binary allocation provides better risk-adjusted returns")
            
            if ladder_drawdown < binary_drawdown:
                print(f"   ✓ Laddering reduces maximum drawdown")
            else:
                print(f"   ✓ Binary allocation has lower maximum drawdown")
        
        print(f"\n2. EXIT STRATEGY RECOMMENDATIONS:")
        
        # Find best strategy for different metrics
        best_sharpe = max(strategies, key=lambda x: x['Sharpe Ratio'])
        best_sortino = max(strategies, key=lambda x: x['Sortino Ratio'])
        min_drawdown = min(strategies, key=lambda x: abs(x['Max Drawdown (%)']))
        
        print(f"   • Best Risk-Adjusted Returns: {best_sharpe['Strategy']}")
        print(f"   • Best Downside Protection: {best_sortino['Strategy']}")
        print(f"   • Lowest Drawdown: {min_drawdown['Strategy']}")
        
        print(f"\n3. TRADING IMPLICATIONS:")
        
        for strategy in strategies:
            trades_per_year = strategy['Trades per Year']
            avg_allocation = strategy['Avg Allocation (%)']
            print(f"   • {strategy['Strategy'][:20]}: {trades_per_year:.1f} trades/year, {avg_allocation:.1f}% avg allocation")
        
        print(f"\n4. FINAL RECOMMENDATION:")
        
        # Determine best overall strategy
        # Weight Sharpe ratio and drawdown equally
        strategy_scores = []
        for strategy in strategies:
            sharpe_score = strategy['Sharpe Ratio']
            drawdown_score = 1 / (abs(strategy['Max Drawdown (%)']) / 100)  # Lower drawdown = higher score
            combined_score = (sharpe_score + drawdown_score) / 2
            strategy_scores.append((strategy['Strategy'], combined_score, sharpe_score, drawdown_score))
        
        best_strategy = max(strategy_scores, key=lambda x: x[1])
        
        print(f"   🏆 RECOMMENDED STRATEGY: {best_strategy[0]}")
        print(f"      Combined Score: {best_strategy[1]:.2f} (Sharpe: {best_strategy[2]:.2f}, Drawdown Score: {best_strategy[3]:.2f})")
        
        # Save results
        binary_exit_portfolio.to_csv('binary_exit_strategy_results.csv')
        pure_binary_portfolio.to_csv('pure_binary_strategy_results.csv')
        
        print(f"\nDetailed results saved to CSV files")
        
        return {
            'binary_exit': binary_exit_metrics,
            'pure_binary': pure_binary_metrics,
            'symmetric': symmetric_metrics,
            'recommendation': best_strategy[0]
        }

def main():
    """Run the optimal laddering analysis"""
    analyzer = OptimalLadderingAnalysis(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        results = analyzer.analyze_exit_strategies()
        return analyzer, results
        
    except Exception as e:
        print(f"Error running optimal laddering analysis: {e}")
        return None, None

if __name__ == "__main__":
    analyzer, results = main()
