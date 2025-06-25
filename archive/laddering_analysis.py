#!/usr/bin/env python3
"""
Laddering Strategy Analysis: Symmetric vs Asymmetric Allocation
Testing different approaches to position sizing based on signal strength
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class LadderingAnalysis:
    def __init__(self, start_date="2012-12-13", end_date=None, initial_capital=55000):
        self.start_date = start_date
        self.end_date = end_date if end_date else datetime.now().strftime('%Y-%m-%d')
        self.initial_capital = initial_capital
        self.data = {}
        
    def fetch_data(self):
        """Fetch historical data for TQQQ and LQQ3.L"""
        print("Fetching data for laddering analysis...")
        
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
        tqqq_data['MACD_Change'] = tqqq_data['MACD_Bullish'].diff()
        tqqq_data['SMA_Change'] = tqqq_data['SMA_Bullish'].diff()
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
                          'MACD_Bullish', 'SMA_Bullish', 'Bullish_Count',
                          'MACD_Change', 'SMA_Change', 'Count_Change']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill missing data
        for col in ['MACD_Bullish', 'SMA_Bullish', 'Bullish_Count']:
            signals_df[col] = signals_df[col].fillna(method='ffill')
        
        for col in ['MACD_Change', 'SMA_Change', 'Count_Change']:
            signals_df[col] = signals_df[col].fillna(0)
        
        # Drop rows without LQQ3 data
        signals_df = signals_df.dropna(subset=['LQQ3_Close'])
        
        print(f"Signals calculated for {len(signals_df)} trading days")
        return signals_df
    
    def run_symmetric_strategy(self, signals):
        """Run symmetric laddering strategy (current approach)"""
        print("Running symmetric laddering strategy...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            bullish_count = row['Bullish_Count']
            count_change = row['Count_Change']
            
            # Target allocations based on signal count
            if bullish_count == 0:
                target_allocation = 0.33
            elif bullish_count == 1:
                target_allocation = 0.66
            else:  # bullish_count == 2
                target_allocation = 1.0
            
            # Current portfolio value
            portfolio_value = cash + shares * lqq3_price
            target_equity_value = portfolio_value * target_allocation
            target_shares = target_equity_value / lqq3_price
            
            # Execute rebalancing if signal changed
            if count_change != 0:
                shares_diff = target_shares - shares
                
                if shares_diff > 0:  # Need to buy
                    cost = shares_diff * lqq3_price
                    if cash >= cost:
                        shares += shares_diff
                        cash -= cost
                        trade_type = 'BUY'
                        trade_amount = shares_diff
                    else:
                        # Buy as much as possible
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
                        # Sell all shares
                        cash += shares * lqq3_price
                        trade_amount = shares
                        shares = 0
                        trade_type = 'SELL'
            else:
                trade_type = 'HOLD'
                trade_amount = 0
            
            # Calculate final portfolio value
            portfolio_value = cash + shares * lqq3_price
            equity_allocation = (shares * lqq3_price) / portfolio_value if portfolio_value > 0 else 0
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'Bullish_Count': bullish_count,
                'Target_Allocation': target_allocation,
                'Actual_Allocation': equity_allocation,
                'Cash': cash,
                'Shares': shares,
                'Portfolio_Value': portfolio_value,
                'Trade_Type': trade_type,
                'Trade_Amount': trade_amount
            })
        
        return pd.DataFrame(portfolio_data)
    
    def run_asymmetric_strategy(self, signals):
        """Run asymmetric laddering strategy (buy in stages, sell more aggressively)"""
        print("Running asymmetric laddering strategy...")
        
        portfolio_data = []
        cash = self.initial_capital
        shares = 0
        
        for date, row in signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            bullish_count = row['Bullish_Count']
            count_change = row['Count_Change']
            macd_change = row['MACD_Change']
            sma_change = row['SMA_Change']
            
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
                        # Buy as much as possible
                        shares_to_buy = cash / lqq3_price
                        shares += shares_to_buy
                        cash = 0
                        trade_type = 'BUY'
                        trade_amount = shares_to_buy
            
            # SELL LOGIC: More aggressive exit
            elif count_change < 0:  # Signal deteriorated
                if bullish_count == 1:  # 2 -> 1 signal: sell back to 66%
                    target_allocation = 0.66
                elif bullish_count == 0:  # 1 -> 0 signals: sell to 33%
                    target_allocation = 0.33
                else:
                    target_allocation = current_allocation
                
                # Additional aggressive sell rule: if we're at 100% and ANY signal turns bearish
                if current_allocation >= 0.95 and (macd_change == -1 or sma_change == -1):
                    target_allocation = 0.33  # Sell directly to minimum allocation
                
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
                        # Sell all shares
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
    
    def run_buy_only_ladder_strategy(self, signals):
        """Run strategy where we ladder in on buys but exit completely on any sell signal"""
        print("Running buy-only laddering strategy...")
        
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
            
            # BUY LOGIC: Ladder in based on signal strength (same as symmetric)
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
            
            # SELL LOGIC: Exit to minimum allocation (33%) when ANY signal deteriorates
            elif count_change < 0:  # Any signal deteriorated
                target_allocation = 0.33
                
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
    
    def calculate_performance_metrics(self, portfolio, strategy_name):
        """Calculate performance metrics for a strategy"""
        portfolio = portfolio.copy()
        portfolio.set_index('Date', inplace=True)
        
        # Calculate returns
        portfolio['Daily_Return'] = portfolio['Portfolio_Value'].pct_change()
        portfolio['Cumulative_Return'] = (portfolio['Portfolio_Value'] / self.initial_capital - 1) * 100
        
        # Buy and hold benchmark
        portfolio['BuyHold_Value'] = (self.initial_capital * 
                                     portfolio['LQQ3_Price'] / 
                                     portfolio['LQQ3_Price'].iloc[0])
        portfolio['BuyHold_Return'] = (portfolio['BuyHold_Value'] / self.initial_capital - 1) * 100
        
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
        
        # Sortino ratio (downside deviation)
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
        if 'Equity_Allocation' in portfolio.columns:
            avg_allocation = portfolio['Equity_Allocation'].mean()
        elif 'Actual_Allocation' in portfolio.columns:
            avg_allocation = portfolio['Actual_Allocation'].mean()
        else:
            avg_allocation = 0
        
        years = (portfolio.index[-1] - portfolio.index[0]).days / 365.25
        
        return {
            'Strategy': strategy_name,
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buyhold_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Final Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Sortino Ratio': round(sortino_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Number of Trades': num_trades,
            'Trades per Year': round(num_trades / years, 1),
            'Avg Allocation (%)': round(avg_allocation * 100, 1)
        }
    
    def compare_strategies(self):
        """Compare all three laddering strategies"""
        print("="*80)
        print("LADDERING STRATEGY COMPARISON")
        print("="*80)
        
        # Fetch data and calculate signals
        self.fetch_data()
        signals = self.calculate_signals()
        
        # Run all strategies
        symmetric_portfolio = self.run_symmetric_strategy(signals)
        asymmetric_portfolio = self.run_asymmetric_strategy(signals)
        buy_only_portfolio = self.run_buy_only_ladder_strategy(signals)
        
        # Calculate performance metrics
        symmetric_metrics = self.calculate_performance_metrics(symmetric_portfolio, "Symmetric Laddering")
        asymmetric_metrics = self.calculate_performance_metrics(asymmetric_portfolio, "Asymmetric Laddering")
        buy_only_metrics = self.calculate_performance_metrics(buy_only_portfolio, "Buy-Only Laddering")
        
        # Display comparison
        all_metrics = [symmetric_metrics, asymmetric_metrics, buy_only_metrics]
        
        print(f"\nPERFORMANCE COMPARISON:")
        print("-"*80)
        
        # Print header
        metrics_order = ['Strategy', 'Total Return (%)', 'Excess Return (%)', 'Volatility (%)', 
                        'Sharpe Ratio', 'Sortino Ratio', 'Max Drawdown (%)', 'Number of Trades', 'Avg Allocation (%)']
        
        print(f"{'Metric':<20}", end="")
        for metrics in all_metrics:
            print(f"{metrics['Strategy'][:18]:<20}", end="")
        print()
        print("-"*80)
        
        for metric in metrics_order[1:]:  # Skip strategy name
            print(f"{metric:<20}", end="")
            for metrics in all_metrics:
                value = metrics[metric]
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
        print("STRATEGY ANALYSIS")
        print("="*80)
        
        # Analyze which is best
        best_sharpe = max(all_metrics, key=lambda x: x['Sharpe Ratio'])
        best_sortino = max(all_metrics, key=lambda x: x['Sortino Ratio'])
        best_return = max(all_metrics, key=lambda x: x['Total Return (%)'])
        min_drawdown = min(all_metrics, key=lambda x: abs(x['Max Drawdown (%)']))
        
        print(f"Best Risk-Adjusted Return (Sharpe): {best_sharpe['Strategy']}")
        print(f"Best Downside Risk (Sortino): {best_sortino['Strategy']}")
        print(f"Highest Total Return: {best_return['Strategy']}")
        print(f"Lowest Maximum Drawdown: {min_drawdown['Strategy']}")
        
        # Strategy descriptions
        print(f"\nSTRATEGY DESCRIPTIONS:")
        print(f"• Symmetric Laddering: 33%/66%/100% allocation based on 0/1/2 bullish signals")
        print(f"• Asymmetric Laddering: Ladder in gradually, exit more aggressively")
        print(f"• Buy-Only Laddering: Ladder in on buys (66%→100%), exit to 33% on any sell")
        
        # Save detailed results
        symmetric_portfolio.to_csv('symmetric_laddering_results.csv')
        asymmetric_portfolio.to_csv('asymmetric_laddering_results.csv')
        buy_only_portfolio.to_csv('buy_only_laddering_results.csv')
        
        print(f"\nDetailed results saved to CSV files")
        
        return {
            'symmetric': symmetric_metrics,
            'asymmetric': asymmetric_metrics,
            'buy_only': buy_only_metrics,
            'portfolios': {
                'symmetric': symmetric_portfolio,
                'asymmetric': asymmetric_portfolio,
                'buy_only': buy_only_portfolio
            }
        }

def main():
    """Run the laddering strategy analysis"""
    analyzer = LadderingAnalysis(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        results = analyzer.compare_strategies()
        return analyzer, results
        
    except Exception as e:
        print(f"Error running laddering analysis: {e}")
        return None, None

if __name__ == "__main__":
    analyzer, results = main()
