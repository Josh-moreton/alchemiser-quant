#!/usr/bin/env python3
"""
Final Variable Allocation Strategy Implementation
Complete backtesting and current signal analysis

Strategy Rules:
- Both BEARISH: 33% LQQ3, 67% Cash
- One BULLISH: 66% LQQ3, 34% Cash
- Both BULLISH: 100% LQQ3, 0% Cash
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
        
    def fetch_data(self):
        """Fetch historical data"""
        print("Fetching data for Variable Allocation Strategy...")
        
        # Fetch TQQQ and LQQ3 data
        tqqq = yf.download('TQQQ', start=self.start_date, end=self.end_date, progress=False)
        lqq3 = yf.download('LQQ3.L', start=self.start_date, end=self.end_date, progress=False)
        
        if tqqq.empty or lqq3.empty:
            raise ValueError("Failed to fetch data")
        
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
        
        # Calculate MACD
        ema_12 = tqqq_data['Close'].ewm(span=12).mean()
        ema_26 = tqqq_data['Close'].ewm(span=26).mean()
        tqqq_data['MACD'] = ema_12 - ema_26
        tqqq_data['MACD_Signal'] = tqqq_data['MACD'].ewm(span=9).mean()
        
        # Calculate 200-day SMA
        tqqq_data['SMA_200'] = tqqq_data['Close'].rolling(window=200).mean()
        
        # Individual signals
        tqqq_data['MACD_Bullish'] = (tqqq_data['MACD'] > tqqq_data['MACD_Signal']).astype(int)
        tqqq_data['SMA_Bullish'] = (tqqq_data['Close'] > tqqq_data['SMA_200']).astype(int)
        
        # Calculate allocation percentages
        tqqq_data['Bullish_Count'] = tqqq_data['MACD_Bullish'] + tqqq_data['SMA_Bullish']
        
        # Variable allocation based on signal count
        conditions = [
            tqqq_data['Bullish_Count'] == 0,  # Both bearish
            tqqq_data['Bullish_Count'] == 1,  # One bullish
            tqqq_data['Bullish_Count'] == 2   # Both bullish
        ]
        allocations = [33, 66, 100]  # LQQ3 allocation percentages
        
        tqqq_data['LQQ3_Allocation'] = np.select(conditions, allocations, default=33)
        
        # Align with LQQ3 data
        lqq3_data = self.data['LQQ3'].copy()
        
        # Find common date range
        start_date = max(lqq3_data.index.min(), tqqq_data.index.min())
        end_date = min(lqq3_data.index.max(), tqqq_data.index.max())
        
        # Filter and merge
        lqq3_filtered = lqq3_data.loc[start_date:end_date].copy()
        tqqq_filtered = tqqq_data.loc[start_date:end_date].copy()
        
        self.signals = pd.merge(
            lqq3_filtered[['Close']].rename(columns={'Close': 'LQQ3_Close'}),
            tqqq_filtered[['Close', 'MACD', 'MACD_Signal', 'SMA_200', 
                          'MACD_Bullish', 'SMA_Bullish', 'Bullish_Count', 'LQQ3_Allocation']].rename(
                columns={'Close': 'TQQQ_Close'}
            ),
            left_index=True,
            right_index=True,
            how='outer'
        )
        
        # Forward fill and clean
        for col in ['MACD_Bullish', 'SMA_Bullish', 'Bullish_Count', 'LQQ3_Allocation']:
            self.signals[col] = self.signals[col].fillna(method='ffill')
        
        self.signals = self.signals.dropna(subset=['LQQ3_Close'])
        
        print(f"Signals calculated for {len(self.signals)} trading days")
        return self.signals
    
    def run_backtest(self):
        """Run variable allocation backtest"""
        print("Running Variable Allocation backtest...")
        
        portfolio_data = []
        total_value = self.initial_capital
        
        for date, row in self.signals.iterrows():
            lqq3_price = row['LQQ3_Close']
            target_allocation = row['LQQ3_Allocation'] / 100  # Convert to decimal
            
            # Calculate target values
            target_lqq3_value = total_value * target_allocation
            target_cash_value = total_value * (1 - target_allocation)
            
            # Calculate shares (assuming we can buy fractional shares)
            lqq3_shares = target_lqq3_value / lqq3_price
            cash = target_cash_value
            
            # Total portfolio value
            portfolio_value = lqq3_shares * lqq3_price + cash
            
            portfolio_data.append({
                'Date': date,
                'LQQ3_Price': lqq3_price,
                'TQQQ_Price': row['TQQQ_Close'],
                'MACD_Bullish': row['MACD_Bullish'],
                'SMA_Bullish': row['SMA_Bullish'],
                'Bullish_Count': row['Bullish_Count'],
                'LQQ3_Allocation_Pct': row['LQQ3_Allocation'],
                'LQQ3_Shares': lqq3_shares,
                'LQQ3_Value': lqq3_shares * lqq3_price,
                'Cash': cash,
                'Portfolio_Value': portfolio_value
            })
            
            # Update total value for next iteration
            total_value = portfolio_value
        
        self.portfolio = pd.DataFrame(portfolio_data)
        self.portfolio.set_index('Date', inplace=True)
        
        print(f"Backtest completed for {len(self.portfolio)} days")
        return self.portfolio
    
    def calculate_metrics(self):
        """Calculate performance metrics"""
        # Calculate returns
        self.portfolio['Daily_Return'] = self.portfolio['Portfolio_Value'].pct_change()
        self.portfolio['Cumulative_Return'] = (self.portfolio['Portfolio_Value'] / self.initial_capital - 1) * 100
        
        # Buy and hold benchmark
        self.portfolio['BuyHold_Value'] = (self.initial_capital * 
                                         self.portfolio['LQQ3_Price'] / 
                                         self.portfolio['LQQ3_Price'].iloc[0])
        self.portfolio['BuyHold_Return'] = (self.portfolio['BuyHold_Value'] / self.initial_capital - 1) * 100
        
        # Performance calculations
        final_value = self.portfolio['Portfolio_Value'].iloc[-1]
        buyhold_final = self.portfolio['BuyHold_Value'].iloc[-1]
        
        total_return = (final_value / self.initial_capital - 1) * 100
        buyhold_return = (buyhold_final / self.initial_capital - 1) * 100
        excess_return = total_return - buyhold_return
        
        # Risk metrics
        daily_returns = self.portfolio['Daily_Return'].dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() != 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = daily_returns[daily_returns < 0]
        downside_std = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0
        sortino_ratio = daily_returns.mean() / downside_std * np.sqrt(252) if downside_std != 0 else 0
        
        # Maximum drawdown
        rolling_max = self.portfolio['Portfolio_Value'].expanding().max()
        drawdown = (self.portfolio['Portfolio_Value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # Allocation statistics
        allocation_stats = self.portfolio['LQQ3_Allocation_Pct'].value_counts().sort_index()
        total_days = len(self.portfolio)
        
        years = (self.portfolio.index[-1] - self.portfolio.index[0]).days / 365.25
        
        return {
            'Total Return (%)': round(total_return, 2),
            'Buy & Hold Return (%)': round(buyhold_return, 2),
            'Excess Return (%)': round(excess_return, 2),
            'Final Value (£)': round(final_value, 2),
            'Volatility (%)': round(volatility, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2),
            'Sortino Ratio': round(sortino_ratio, 2),
            'Max Drawdown (%)': round(max_drawdown, 2),
            'Years': round(years, 1),
            'Allocation Stats': {
                '33% Days': allocation_stats.get(33, 0),
                '66% Days': allocation_stats.get(66, 0), 
                '100% Days': allocation_stats.get(100, 0),
                '33% Pct': round(allocation_stats.get(33, 0) / total_days * 100, 1),
                '66% Pct': round(allocation_stats.get(66, 0) / total_days * 100, 1),
                '100% Pct': round(allocation_stats.get(100, 0) / total_days * 100, 1)
            }
        }
    
    def get_current_status(self):
        """Get current signal status"""
        latest = self.signals.iloc[-1]
        
        return {
            'date': latest.name,
            'tqqq_price': latest['TQQQ_Close'],
            'lqq3_price': latest['LQQ3_Close'],
            'macd_bullish': bool(latest['MACD_Bullish']),
            'sma_bullish': bool(latest['SMA_Bullish']),
            'bullish_count': int(latest['Bullish_Count']),
            'allocation_pct': int(latest['LQQ3_Allocation'])
        }
    
    def print_summary(self):
        """Print comprehensive summary"""
        metrics = self.calculate_metrics()
        current = self.get_current_status()
        
        print("="*80)
        print("VARIABLE ALLOCATION STRATEGY - FINAL RESULTS")
        print("="*80)
        print("Strategy: Variable allocation based on signal strength")
        print("• Both BEARISH: 33% LQQ3, 67% Cash")
        print("• One BULLISH: 66% LQQ3, 34% Cash") 
        print("• Both BULLISH: 100% LQQ3, 0% Cash")
        print(f"Period: {self.signals.index[0].strftime('%Y-%m-%d')} to {self.signals.index[-1].strftime('%Y-%m-%d')}")
        print(f"Initial Capital: £{self.initial_capital:,}")
        print("-"*80)
        
        print("PERFORMANCE METRICS:")
        print(f"  Total Return              : {metrics['Total Return (%)']}%")
        print(f"  Buy & Hold Return         : {metrics['Buy & Hold Return (%)']}%")
        print(f"  Excess Return             : {metrics['Excess Return (%)']}%")
        print(f"  Final Portfolio Value     : £{metrics['Final Value (£)']:,.2f}")
        print(f"  Volatility                : {metrics['Volatility (%)']}%")
        print(f"  Sharpe Ratio              : {metrics['Sharpe Ratio']}")
        print(f"  Sortino Ratio             : {metrics['Sortino Ratio']}")
        print(f"  Maximum Drawdown          : {metrics['Max Drawdown (%)']}%")
        
        print("\nALLOCATION DISTRIBUTION:")
        stats = metrics['Allocation Stats']
        print(f"  33% LQQ3 (Defensive)      : {stats['33% Days']} days ({stats['33% Pct']}%)")
        print(f"  66% LQQ3 (Balanced)       : {stats['66% Days']} days ({stats['66% Pct']}%)")
        print(f"  100% LQQ3 (Aggressive)    : {stats['100% Days']} days ({stats['100% Pct']}%)")
        
        print("-"*80)
        print("CURRENT STATUS:")
        print(f"  Date                      : {current['date'].strftime('%Y-%m-%d')}")
        print(f"  TQQQ Price                : ${current['tqqq_price']:.2f}")
        print(f"  LQQ3 Price                : £{current['lqq3_price']:.2f}")
        
        macd_status = "🟢 BULLISH" if current['macd_bullish'] else "🔴 BEARISH"
        sma_status = "🟢 BULLISH" if current['sma_bullish'] else "🔴 BEARISH"
        
        print(f"  MACD Signal               : {macd_status}")
        print(f"  SMA Signal                : {sma_status}")
        print(f"  Bullish Signals           : {current['bullish_count']}/2")
        print(f"  Current Allocation        : {current['allocation_pct']}% LQQ3")
        
        if current['allocation_pct'] == 33:
            stance = "🛡️ DEFENSIVE"
        elif current['allocation_pct'] == 66:
            stance = "⚖️ BALANCED" 
        else:
            stance = "🚀 AGGRESSIVE"
            
        print(f"  Market Stance             : {stance}")
        print("="*80)
        
        return metrics, current

def main():
    """Run the complete variable allocation strategy"""
    print("VARIABLE ALLOCATION STRATEGY - COMPLETE ANALYSIS")
    print("Optimized risk-adjusted returns through dynamic allocation")
    print()
    
    strategy = VariableAllocationStrategy(
        start_date="2012-12-13",
        initial_capital=55000
    )
    
    try:
        # Run complete analysis
        strategy.fetch_data()
        strategy.calculate_signals()
        strategy.run_backtest()
        
        # Display results
        metrics, current = strategy.print_summary()
        
        # Save results
        strategy.portfolio.to_csv('variable_allocation_strategy_results.csv')
        print(f"\nDetailed results saved to 'variable_allocation_strategy_results.csv'")
        
        return strategy
        
    except Exception as e:
        print(f"Error running strategy: {e}")
        return None

if __name__ == "__main__":
    strategy = main()
